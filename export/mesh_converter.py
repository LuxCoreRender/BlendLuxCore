import os
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from time import time
import numpy as np

_needs_reload = "bpy" in locals()

import bpy
import pyluxcore

from . import caches
from .. import utils
from ..utils.errorlog import LuxCoreErrorLog

if _needs_reload:
    import importlib

    importlib.reload(caches)
    importlib.reload(utils)


# Reserved triangle AOV layer holding the material slot index of each
# triangle (face-varying data bound to the mesh, like UVs). Indices 0 and 1
# are used by TriAOVDataIndices (random per island). LuxCore reads this layer
# to split the C++ subdiv envelope back per material.
MATERIAL_TRI_AOV_INDEX = 2

# Islands (varying-data connected components) smaller than this many
# triangles are merged into an adjacent island at export (avoids tiny
# fragments / thousands of submeshes on big models)
MIN_ISLAND_TRIANGLE_COUNT = 64
# Small islands are merged into an adjacent island only when the angle
# between the two sides' normals is below this (hard edges are kept)
MIN_ISLAND_MERGE_COS_ANGLE = float(np.cos(np.deg2rad(30.0)))

# Verbose per-submesh logging (off by default: printing thousands of submeshes
# is a measurable cost on fragment-heavy models)
_DEBUG_MESH = bool(os.environ.get("BLC_DEBUG_MESH"))


# https://blenderartists.org/t/\
# efficient-copying-of-vertex-coords-to-and-from-numpy-arrays/661467/2
def get_ndarray(
    bpy_collection: bpy.types.bpy_prop_collection,
    attr: str,
    stride: int,
    dtype: np.dtype,
):
    """Get a numpy array from a Blender collection.

    If stride == 0, the array is raveled
    """
    count = len(bpy_collection)
    buffer = np.empty(shape=(count, stride if stride else 1), dtype=dtype)
    bpy_collection.foreach_get(attr, np.ravel(buffer))
    if not stride:
        buffer = buffer.ravel()
    return buffer



def _sortable_float_bits(values):
    """Order-preserving uint32 keys of a contiguous float32 array.

    Transforms the float bits so that uint32 comparison order matches float
    order; -0.0 is mapped to the +0.0 key so it compares equal (as np.unique
    does).
    """
    bits = values.view(np.uint32)
    keys = bits ^ np.where(bits >> 31 == 1, np.uint32(0xFFFFFFFF), np.uint32(0x80000000))
    return np.where(bits == np.uint32(0x80000000), np.uint32(0), keys)


def _weld_points(vertex_points):
    """Weld coincident points.

    Same result as
    np.unique(vertex_points, axis=0, return_index=True, return_inverse=True),
    but faster: the two first coordinates are packed into a single uint64
    sort key (order-preserving float bits), so the weld is a lexicographic
    sort over 8-byte keys instead of a sort over 12-byte voids.
    """
    n = len(vertex_points)
    if n == 0:
        return (vertex_points.reshape(0, 3), np.zeros(0, dtype=np.int64),
                np.zeros(0, dtype=np.int64))
    if np.isnan(vertex_points).any():
        # NaN payloads are not bit-identical; fall back to exact unique
        return np.unique(vertex_points, axis=0, return_index=True, return_inverse=True)
    keys = _sortable_float_bits(np.ascontiguousarray(vertex_points))
    key64 = (keys[:, 0].astype(np.uint64) << 32) | keys[:, 1].astype(np.uint64)
    # Lexicographic (x, y, z) order: the packed (x, y) key with z as
    # secondary key, so that fully equal points are adjacent and the
    # boundary detection below sees them
    order = _argsort(key64, keys[:, 2])
    k64 = key64[order]
    z = keys[:, 2][order]
    same = (k64[1:] == k64[:-1]) & (z[1:] == z[:-1])
    boundary = np.empty(n, dtype=bool)
    boundary[0] = True
    boundary[1:] = ~same
    first_index = order[boundary]
    group = np.cumsum(boundary) - 1
    weld_inverse = np.empty(n, dtype=np.int64)
    weld_inverse[order] = group
    return vertex_points[first_index], first_index, weld_inverse


# Serializes LuxCore scene mutations (DefineMeshExt, SetMeshTriangleAOV) when
# the compute phase runs in worker threads
_SCENE_LOCK = threading.Lock()

# Below this size, np.argsort is faster than the parallel C++ sort
_ARGSORT_PARALLEL_MIN_SIZE = 1 << 20

_parallel_argsort = getattr(pyluxcore, "parallel_argsort", None)


def _argsort(keys, secondary=None):
    """argsort of a 1-D array, using the parallel C++ sort (which releases
    the GIL) for large arrays, so worker threads can overlap sorting work.
    With a 1-D 'secondary' array, sorts lexicographically by (keys, secondary).
    Ties are broken by index, so the result is deterministic (stable)."""
    if _parallel_argsort is not None and keys.size >= _ARGSORT_PARALLEL_MIN_SIZE:
        return _parallel_argsort(keys, secondary if secondary is not None else None)
    if secondary is not None:
        return np.lexsort((secondary, keys))
    return np.argsort(keys, kind="stable")


def extract_mesh_data(obj, depsgraph):
    """Read all mesh data from Blender into numpy arrays.

    Must run in the main thread (Blender API access). Returns None for
    objects without a mesh.
    """
    with _prepare_mesh(obj, depsgraph) as mesh:
        if mesh is None:
            return None

        # Blender API may not be always consistent with naming, for the mesh object.
        # For the sake of clarity, we list here our naming conventions.
        # They may specially differ from attribute domains...
        # https://docs.blender.org/api/current/bpy_types_enum_items/attribute_domain_items.html#rna-enum-attribute-domain-items
        # Point: a point in the 3D-space, (float, float, float)
        # Vertex: an index to the mesh array of points
        # Loop: a vertex and an edge

        # Loop vertices: for each loop, the index of the mesh vertex it uses
        loop_vertices = get_ndarray(mesh.loops, "vertex_index", 0, np.uint32)

        # Points (raw, unwelded)
        vertex_points = get_ndarray(mesh.vertices, "co", 3, np.float32)

        # Per-vertex data of the (possibly split) source vertices
        vertex_normals = get_ndarray(mesh.vertices, "normal", 3, np.float32)

        # Per-loop shading normals: corner normals honor flat/smooth faces and
        # custom split normals (fall back to per-vertex normals if unavailable)
        corner_normals = getattr(mesh, "corner_normals", None)
        if corner_normals is not None and len(corner_normals) == len(mesh.loops):
            loop_normals = get_ndarray(corner_normals, "vector", 3, np.float32)
        else:
            loop_normals = vertex_normals[loop_vertices]

        # Triangle loop indices
        triangle_loops = get_ndarray(
            mesh.loop_triangles, "loops", 3, np.uint32
        )

        # Material slot index for each triangle
        loop_triangle_materials = get_ndarray(
            mesh.loop_triangles, "material_index", 1, np.uint32
        ).ravel()

        # UV layers, per-loop in Blender
        loop_uvs = [
            get_ndarray(uv_layer.uv, "vector", 2, np.float32)
            for uv_layer in mesh.uv_layers
        ]

        # Vertex color attributes
        color_attrs = [
            (
                get_ndarray(attribute.data, "color", 4, np.float32),
                attribute.domain,
            )
            for attribute in mesh.color_attributes
        ]

        # Edge creases (raw, per-edge): remapped to welded point pairs later
        edge_verts = None
        edge_crease = None
        crease_attr = mesh.attributes.get("crease_edge")
        if crease_attr is not None and crease_attr.domain == "EDGE":
            edge_verts = get_ndarray(mesh.edges, "vertices", 2, np.int32)
            edge_crease = get_ndarray(crease_attr.data, "value", 0, np.float32)
        vert_crease_attr = mesh.attributes.get("crease_vert")
        if (
            vert_crease_attr is not None
            and vert_crease_attr.domain == "POINT"
            and np.any(get_ndarray(vert_crease_attr.data, "value", 0, np.float32) > 0.0)
        ):
            print(
                "[BLC] Warning: vertex creases (crease_vert) are not exported "
                "(OpenSubdiv topology descriptors only support edge creases)"
            )

        return dict(
            loop_vertices=loop_vertices,
            vertex_points=vertex_points,
            vertex_normals=vertex_normals,
            loop_normals=loop_normals,
            triangle_loops=triangle_loops,
            loop_triangle_materials=loop_triangle_materials,
            loop_uvs=loop_uvs,
            color_attrs=color_attrs,
            edge_verts=edge_verts,
            edge_crease=edge_crease,
        )


_compute_submeshes_c = getattr(pyluxcore, "compute_submeshes_c", None)


def compute_submeshes(data, mesh_key, transform, is_viewport_render, use_instancing,
                      share_points=True):
    """Weld points, find varying-data islands, group triangles by
    (material, island) and gather the per-submesh varying data.

    Uses the C++/TBB implementation in pyluxcore when available
    (BLC_COMPUTE=py forces the numpy fallback). Returns (payloads, info):
    payloads is a list of dicts ready for define_submeshes(), info holds
    log/stat data.

    share_points: when True (objects with a subdivision shape), all submeshes
    share one welded point buffer (the C++ subdiv envelope is built over all
    meshes sharing it). When False, each submesh is compacted to the points it
    actually uses, which saves a lot of memory on fragment-heavy meshes.
    Set BLC_FORCE_SHARE_POINTS=1 to force the shared-point path (debug).
    """
    if os.environ.get("BLC_FORCE_SHARE_POINTS"):
        share_points = True
    if _compute_submeshes_c is not None and os.environ.get("BLC_COMPUTE", "cpp") != "py":
        # Pass the transform only when it will be applied (same condition as
        # the numpy path: not in viewport, not instanced)
        xform = None
        if transform is not None and not (is_viewport_render or use_instancing):
            xform = np.array(
                [[transform[i][j] for j in range(4)] for i in range(4)],
                dtype=np.float32,
            )
        payloads, info = _compute_submeshes_c(
            data["vertex_points"],
            data["loop_vertices"],
            data["loop_normals"],
            data["triangle_loops"],
            data["loop_triangle_materials"],
            data["loop_uvs"],
            [colors for colors, _domain in data["color_attrs"]],
            [domain for _colors, domain in data["color_attrs"]],
            data["edge_verts"],
            data["edge_crease"],
            xform,
            is_viewport_render,
            use_instancing,
            share_points,
            str(mesh_key),
        )
        print(f"[BLC] Exporting '{str(mesh_key)}' - {len(payloads)} submesh(es)")
        print(f"[BLC] - {info['num_points']} welded points (shared between submeshes), "
              f"from {info['num_raw']} raw vertices")
        print(f"[BLC] - {len(data['loop_uvs'])} uv layer(s)" if len(data['loop_uvs']) != 1
              else "[BLC] - 1 uv layer")
        print(f"[BLC] - {len(data['color_attrs'])} color layer(s)" if len(data['color_attrs']) != 1
              else "[BLC] - 1 color layer")
        if os.environ.get("BLC_TIME_STAGES"):
            st = info.get("stages", {})
            print("[BLC-STAGES] " + str(mesh_key) + ": " +
                  " ".join(f"{k}={v:.3f}" for k, v in st.items()), flush=True)
        return payloads, info
    return _compute_submeshes_py(
        data, mesh_key, transform, is_viewport_render, use_instancing, share_points
    )


def _compute_submeshes_py(data, mesh_key, transform, is_viewport_render, use_instancing,
                          share_points=True):
    """Numpy fallback implementation of compute_submeshes (used when the
    pyluxcore build has no compute_submeshes_c, or BLC_COMPUTE=py).
    Pure numpy/pyluxcore (no Blender API): safe to run in worker threads.
    The big sorts and the union-find release the GIL in pyluxcore.
    """
    if os.environ.get("BLC_FORCE_SHARE_POINTS"):
        share_points = True
    start_time = time()
    _stage_t = {} if os.environ.get("BLC_TIME_STAGES") else None
    def _stage(name, t0):
        if _stage_t is not None:
            _stage_t[name] = _stage_t.get(name, 0.0) + (time() - t0)

    loop_vertices = data["loop_vertices"]
    vertex_points = data["vertex_points"]
    vertex_normals = data["vertex_normals"]
    loop_normals = data["loop_normals"]
    triangle_loops = data["triangle_loops"]
    loop_triangle_materials = data["loop_triangle_materials"]
    loop_uvs = data["loop_uvs"]
    color_attrs = data["color_attrs"]

    # Points: weld coincident vertices (the evaluated mesh may contain
    # split vertices, e.g. from split_faces() at sharp edges). Coincident
    # vertices must not stay distinct, otherwise modifiers displacing
    # vertices (like subdivision) would open gaps in the mesh.
    # Discontinuities of varying data (uv...) are handled by submeshes
    # (see UV islands below), not by split vertices.
    # The welded point array is shared by all the submeshes defined below
    # (LuxCore shares the point storage between meshes defined with
    # identical points).
    _t = time()
    welded_points, first_index, weld_inverse = _weld_points(vertex_points)
    _stage('weld', _t); _t = time()
    num_points = len(welded_points)

    # Per-loop varying signature: UVs (all layers) + shading normal.
    # A discontinuity in any of them is a seam (like a UV seam): loops
    # across a shared edge are joined only when the full signature
    # matches at both endpoints.
    if loop_uvs:
        uv_sig = np.stack(loop_uvs, axis=1)  # [n_loops, n_layers, 2]
    else:
        uv_sig = np.zeros((len(loop_vertices), 0, 2), dtype=np.float32)
    loop_sig = np.concatenate(
        [uv_sig.reshape(len(loop_vertices), -1), loop_normals], axis=1
    )

    # Edge creases (used by the subdiv shape in "imported" creases mode):
    # Blender stores them as the float attribute "crease_edge" (EDGE
    # domain, 0..1). Convert to OpenSubdiv sharpness (x10, clamped at
    # 10 = infinite crease) and remap the vertex indices to the welded
    # point indices, so that the pairs index the shared point array.
    crease_pairs = None
    crease_weights = None
    edge_verts = data["edge_verts"]
    edge_crease = data["edge_crease"]
    if edge_verts is not None:
        w0 = weld_inverse[edge_verts[:, 0]]
        w1 = weld_inverse[edge_verts[:, 1]]
        keep = edge_crease > 0.0
        w0, w1, cw = w0[keep], w1[keep], edge_crease[keep]
        # Dedupe: several split edges may weld to the same point pair
        keys = (np.minimum(w0, w1).astype(np.uint64) << 32) | np.maximum(w0, w1).astype(np.uint64)
        _, first = np.unique(keys, return_index=True)
        crease_pairs = np.stack(
            [w0[first], w1[first]], axis=1
        ).astype(np.uint32).ravel()
        crease_weights = np.minimum(cw[first] * 10.0, 10.0).astype(np.float32)

    # --- Varying-data islands (UV seams + normal seams) ----------------------
    # A loop belongs to the island of its (vertex, uv, normal) signature;
    # the two loops at the endpoints of a shared edge are joined when
    # their signatures match, and the 3 loops of a triangle are always
    # joined (a seam cannot run through the interior of a triangle).
    # Triangles of different islands (or materials) are exported as
    # separate submeshes, so that each submesh has consistent per-vertex
    # UVs AND normals over the shared welded points.
    loop_welded = weld_inverse[loop_vertices]
    n_tris = len(triangle_loops)
    n_loops = len(loop_vertices)

    # Per-loop signature bytes (void view), for exact seam comparison
    sig_flat = np.ascontiguousarray(loop_sig)
    sig_void = sig_flat.view(np.dtype((np.void, sig_flat.dtype.itemsize * sig_flat.shape[1]))).ravel()

    # Edge occurrences: for each triangle, edges (c0,c1), (c1,c2), (c2,c0),
    # normalized so the welded endpoint ids are sorted
    e_src = np.stack(
        [triangle_loops, np.roll(triangle_loops, -1, axis=1)], axis=2
    ).reshape(-1, 2)  # [n_tris*3, 2] loop indices
    w0 = loop_welded[e_src[:, 0]]
    w1 = loop_welded[e_src[:, 1]]
    swap = w0 > w1
    e_lo = np.where(swap, w1, w0)
    e_hi = np.where(swap, w0, w1)
    l_lo = np.where(swap, e_src[:, 1], e_src[:, 0])  # loop at lo endpoint
    l_hi = np.where(swap, e_src[:, 0], e_src[:, 1])  # loop at hi endpoint
    e_key = e_lo * num_points + e_hi

    # Sort occurrences by edge only (single key, parallel C++ sort for large
    # meshes): the occurrences of a same edge become one adjacent run
    order = _argsort(e_key)
    k_s = e_key[order]

    # Triangle of each edge occurrence (occurrences are laid out as
    # 3 per triangle, in triangle order)
    tri_of_occurrence = np.repeat(np.arange(n_tris, dtype=np.int64), 3)
    # Triangle that owns each loop (loop_triangles partitions the loops,
    # but the loops of a triangle are not necessarily consecutive, e.g.
    # when triangulating quads)
    tri_of_loop = np.empty(n_loops, dtype=np.int64)
    tri_of_loop[triangle_loops.ravel()] = tri_of_occurrence
    # triangle of each occurrence in the SORTED order
    tri_of_sorted = tri_of_occurrence[order]

    # Union pairs over TRIANGLES (not loops: the 3 loops of a triangle
    # are one node), across each shared edge: consecutive occurrences of
    # the same edge are joined when the full signature matches at both
    # endpoints (chaining joins whole signature groups within an edge
    # run; the run length is 2 for manifold edges). The element space
    # is ~3x smaller than the loop space, which dominates the
    # union-find cost.
    same_edge = np.empty(len(order), dtype=bool)
    same_edge[0] = False
    same_edge[1:] = k_s[1:] == k_s[:-1]
    s_lo = sig_void[l_lo[order]]
    s_hi = sig_void[l_hi[order]]
    join = same_edge[1:] & (s_lo[1:] == s_lo[:-1]) & (s_hi[1:] == s_hi[:-1])
    del s_lo, s_hi
    idx = np.nonzero(join)[0]
    del join
    pairs = (
        np.stack([tri_of_sorted[idx], tri_of_sorted[idx + 1]], axis=1).astype(np.uint32)
        if n_tris else np.zeros((0, 2), dtype=np.uint32)
    )

    # Connected components over triangles, using the parallel C++
    # union-find exposed by pyluxcore (slg::equiv::GroupByEquivalence)
    island = (
        pyluxcore.union_find(n_tris, pairs).astype(np.int64)
        if n_tris
        else np.zeros(0, dtype=np.int64)
    )

    # Merge very small islands into an adjacent island: one submesh per
    # tiny island means many small fragments on big models (each submesh
    # is a full LuxCore mesh with per-point arrays), e.g. dense split
    # normals create tens of thousands of 2-4 triangle islands. Merging
    # only affects the varying data gathered at the shared points (last
    # write wins), so keep the threshold small, and never merge across a
    # hard edge (large angle between the two sides' normals), otherwise
    # flat faces would be smoothed away (e.g. the default cube).
    if n_tris:
        n_islands0 = int(island.max()) + 1
        island_size = np.bincount(island, minlength=n_islands0)
        if os.environ.get("BLC_DEBUG_ISLANDS"):
            hist, edges = np.histogram(island_size, bins=[1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 1 << 30])
            print(f"[BLC] island size histogram for {mesh_key}: " +
                  ", ".join(f"[{edges[i]},{edges[i+1]}): {hist[i]}" for i in range(len(hist))),
                  flush=True)
        small = island_size < MIN_ISLAND_TRIANGLE_COUNT
        if np.any(small):
            # Edge runs (order is already sorted by edge key)
            starts = np.nonzero(np.r_[True, k_s[1:] != k_s[:-1]])[0]
            ends = np.r_[starts[1:] - 1, len(k_s) - 1]
            multi = (ends - starts + 1) >= 2
            l_lo_s = l_lo[order]
            l_hi_s = l_hi[order]
            isl_a = island[tri_of_sorted[starts]]
            isl_b = island[tri_of_sorted[ends]]
            adj = multi & (isl_a != isl_b)
            # angle between the two sides' normals (at both endpoints)
            n1 = loop_normals[l_lo_s[starts]]
            n2 = loop_normals[l_hi_s[ends]]
            cosang = np.einsum("ij,ij->i", n1, n2)
            not_hard = cosang > MIN_ISLAND_MERGE_COS_ANGLE
            any_small = np.zeros(len(starts), dtype=bool)
            any_small[adj] = small[isl_a[adj]] | small[isl_b[adj]]
            merge = adj & any_small & not_hard
            if np.any(merge):
                # Merge at the ISLAND level: a small union-find over the
                # island labels (not over all triangles), then map back,
                # so chains of small islands collapse in one pass
                isl_pairs = np.unique(
                    np.stack([isl_a[merge], isl_b[merge]], axis=1).astype(np.uint32),
                    axis=0,
                )
                isl_map = pyluxcore.union_find(n_islands0, isl_pairs).astype(np.int64)
                island = isl_map[island]

    # Loop island for the per-submesh gathers (island of the loop's tri)
    _stage('islands', _t); _t = time()
    loop_island = island[tri_of_loop]

    n_islands = int(island.max()) + 1 if n_tris else 1

    # Group triangles by (material, island): one sort + split by boundary,
    # instead of one full scan of tri_group per group (O(groups x tris))
    tri_keys = loop_triangle_materials * n_islands + island
    group_keys, tri_group = np.unique(tri_keys, return_inverse=True)
    if len(group_keys) > 64:
        # Many groups: one sort + split by boundary is cheaper than one full
        # scan of tri_group per group (O(groups x tris))
        order = np.argsort(tri_group, kind="stable")
        sorted_g = tri_group[order]
        starts = np.nonzero(np.r_[True, sorted_g[1:] != sorted_g[:-1]])[0]
        ends = np.r_[starts[1:], len(order)]
        groups = {g: order[starts[g]:ends[g]] for g in range(len(group_keys))}
    else:
        groups = {}
        for g in range(len(group_keys)):
            groups[g] = np.nonzero(tri_group == g)[0]
    _stage('group', _t); _t = time()

    # Transformation: bake it into the welded points and pre-rotate the loop
    # normals here in numpy (the parallel compute phase), instead of passing
    # it to DefineMeshExt, which would deep-copy + rotate the normals of
    # EVERY submesh in the serial define phase. Negative-determinant
    # transforms (mirror) keep the C++ path, which handles the handedness
    # flip.
    normals_pretransformed = False
    if is_viewport_render or use_instancing:
        mesh_transform = None
    else:
        mesh_transform = np.array(
            [
                transform[0][0:4],
                transform[1][0:4],
                transform[2][0:4],
                transform[3][0:4],
            ],
            dtype=np.float32,
        )
        rot = mesh_transform[:3, :3]
        if np.linalg.det(rot) > 0.0:
            welded_points = (
                welded_points @ rot.T + mesh_transform[:3, 3]
            ).astype(np.float32)
            # Normal transform is the inverse-transpose of the rotation:
            # n' = (R^-1)^T n, i.e. n_row @ R^-1 in numpy
            rot_inv = np.linalg.inv(rot).astype(np.float32)
            loop_normals = loop_normals @ rot_inv
            norms = np.linalg.norm(loop_normals, axis=1, keepdims=True)
            loop_normals = (loop_normals / np.maximum(norms, 1e-30)).astype(np.float32)
            mesh_transform = None
            normals_pretransformed = True

    # Log
    def fmt_layer(layers, layer_name):
        nlayers = len(layers)
        suffix = "layers" if nlayers > 1 else "layer"
        return f"{nlayers} {layer_name} {suffix}"
    print(f"[BLC] Exporting '{str(mesh_key)}' - {len(groups)} submesh(es)")
    print(f"[BLC] - {num_points} welded points (shared between submeshes), "
          f"from {len(vertex_points)} raw vertices")
    print(f"[BLC] - {fmt_layer(loop_uvs, 'uv layer')}")
    print(f"[BLC] - {fmt_layer(color_attrs, 'color layer')}")

    # Candidate per-object shared arrays for corner-domain attributes (one
    # value per welded point; where loops disagree at a seam, the last writer
    # wins). A submesh shares a candidate only if all of its loops carry
    # exactly the candidate values -- then the zero-copy wrap hands the same
    # numpy memory to LuxCore for every such submesh, with no per-submesh
    # allocation or C++ copy.
    def _candidate(loop_data):
        cand = np.empty((num_points, loop_data.shape[1]), dtype=np.float32)
        cand[loop_welded] = loop_data
        return cand

    _stage('sig_edges', _t); _t = time()
    uv_candidates = [_candidate(loop_uv) for loop_uv in loop_uvs]
    normal_candidate = _candidate(loop_normals)
    # Keep rgb and alpha as separate contiguous arrays so a shared candidate
    # stays contiguous (a [:, :3] view would force a copy in pyluxcore)
    # POINT-domain colors are per-vertex: weld them once and share the
    # contiguous rgb/alpha arrays between all submeshes
    point_colors = [
        (colors[first_index][:, :3].copy(), colors[first_index][:, 3:4].copy())
        if domain == "POINT" else (None, None)
        for colors, domain in color_attrs
    ]
    # Contiguous rgb/alpha views per color attribute, computed once per
    # object (slicing per submesh would gather from a strided array)
    corner_colors = [
        (np.ascontiguousarray(colors[:, :3]), np.ascontiguousarray(colors[:, 3:4]))
        if domain == "CORNER" else (None, None)
        for colors, domain in color_attrs
    ]
    color_candidates = [
        (_candidate(rgb), _candidate(alpha))
        if rgb is not None else (None, None)
        for rgb, alpha in corner_colors
    ]

    def _submesh_attr(cand, loop_data, g_loop_flat, gw_flat, isl_loops, isl_gw):
        # Share the candidate if every loop of this submesh (its triangles
        # index all of them, not only the island's) agrees with it
        if cand is not None and np.array_equal(loop_data[g_loop_flat], cand[gw_flat]):
            return cand
        arr = np.empty((num_points, loop_data.shape[1]), dtype=np.float32)
        arr[isl_gw] = loop_data[isl_loops]
        return arr

    def _compact_attr(loop_data, g_loop_flat, local_idx, n_used):
        # Per-submesh compact attribute array: one row per used point, filled
        # from the submesh's corners (last corner wins at a shared point, same
        # semantics as the shared-buffer gather above)
        arr = np.empty((n_used, loop_data.shape[1]), dtype=np.float32)
        arr[local_idx] = loop_data[g_loop_flat]
        return arr

    payloads = []
    first_submesh_name = None
    for g in sorted(groups.keys()):
        gkey = int(group_keys[g])
        mat = gkey // n_islands
        isl = gkey % n_islands
        g_tris = groups[g]
        g_loops = triangle_loops[g_tris]       # [g, 3] loop indices
        g_loop_flat = g_loops.ravel()
        gw = loop_welded[g_loops]              # welded vertex per corner
        name = f"{str(mesh_key)}{mat:03d}i{isl:03d}"

        _t2 = time()
        if share_points:
            # Remap the triangle loop indices to welded vertex indices, so
            # that all the submeshes index the same shared welded point array
            # (uint32, as expected by pyluxcore)
            sub_triangles = gw.astype(np.uint32)

            # Loops of this submesh that belong to this island (a triangle
            # corner at a seam vertex may belong to another island)
            isl_mask = loop_island[g_loop_flat] == isl
            isl_loops = g_loop_flat[isl_mask]
            isl_gw = gw.ravel()[isl_mask]

            # Per-submesh varying data, gathered from this island's loops
            # (consistent within the island by construction), aligned with
            # the shared welded points. Corner-domain attributes fall back to
            # a shared per-object array when this submesh has no seam for them
            # (see _submesh_attr); points outside the submesh's islands are
            # never referenced by its triangles, so their values are never read.
            gw_flat = gw.ravel()
            sub_uvs = [
                _submesh_attr(cand, loop_uv, g_loop_flat, gw_flat, isl_loops, isl_gw)
                for cand, loop_uv in zip(uv_candidates, loop_uvs)
            ]
            sub_normals = _submesh_attr(
                normal_candidate, loop_normals, g_loop_flat, gw_flat, isl_loops, isl_gw
            )
            sub_rgb, sub_alphas = [], []
            for (rgb, alpha), domain, (rgb_cand, alpha_cand), (pt_rgb, pt_alpha) in zip(
                corner_colors, [d for _, d in color_attrs], color_candidates, point_colors
            ):
                if domain == "POINT":
                    sub_rgb.append(pt_rgb)
                    sub_alphas.append(pt_alpha)
                elif domain == "CORNER":
                    sub_rgb.append(_submesh_attr(
                        rgb_cand, rgb, g_loop_flat, gw_flat, isl_loops, isl_gw
                    ))
                    sub_alphas.append(_submesh_attr(
                        alpha_cand, alpha, g_loop_flat, gw_flat, isl_loops, isl_gw
                    ))
                else:
                    raise ValueError(f"Unhandled attribute domain: '{domain}'")

            # All submeshes share one point buffer: the first submesh owns it
            # (and bakes the transformation into its points), the others
            # reference it by name
            if first_submesh_name is None:
                points = welded_points
                submesh_transform = mesh_transform
                first_submesh_name = name
            else:
                points = first_submesh_name
                submesh_transform = None
            sub_creases = crease_pairs
            sub_crease_weights = crease_weights
        else:
            _stage('pl_gather', _t2); _t2 = time()
            # Compact the submesh to the welded points it actually uses:
            # local point array + remapped triangles + compact attribute
            # arrays. Much less memory than full-object-size arrays per
            # submesh on fragment-heavy meshes.
            used, local_idx = np.unique(gw.ravel(), return_inverse=True)
            sub_triangles = local_idx.reshape(gw.shape).astype(np.uint32)
            points = welded_points[used]
            submesh_transform = mesh_transform
            n_used = len(used)
            sub_uvs = [
                _compact_attr(loop_uv, g_loop_flat, local_idx, n_used)
                for loop_uv in loop_uvs
            ]
            sub_normals = _compact_attr(
                loop_normals, g_loop_flat, local_idx, n_used
            )
            sub_rgb, sub_alphas = [], []
            for (rgb, alpha), domain, (pt_rgb, pt_alpha) in zip(
                corner_colors, [d for _, d in color_attrs], point_colors
            ):
                if domain == "POINT":
                    # Per-vertex colors welded once per object: compact to
                    # the used points (indices remapped like the triangles)
                    sub_rgb.append(pt_rgb[used])
                    sub_alphas.append(pt_alpha[used])
                elif domain == "CORNER":
                    sub_rgb.append(_compact_attr(
                        rgb, g_loop_flat, local_idx, n_used
                    ))
                    sub_alphas.append(_compact_attr(
                        alpha, g_loop_flat, local_idx, n_used
                    ))
                else:
                    raise ValueError(f"Unhandled attribute domain: '{domain}'")
            # Creases are only consumed by subdivision shapes (IMPORTED
            # crease mode); this object has none, so skip them
            sub_creases = None
            sub_crease_weights = None

        _stage('pl_attr', _t2)
        if _DEBUG_MESH and (g < 10 or len(groups) <= 12):
            print(f"[BLC] - Submesh {name}: {len(sub_triangles)} triangles")
        elif _DEBUG_MESH and g == 10:
            print(f"[BLC] - ... ({len(groups) - 10} more submeshes)")

        payloads.append(dict(
            name=name,
            points=points,
            triangles=sub_triangles,
            normals=sub_normals,
            uvs=sub_uvs,
            colors=sub_rgb,
            alphas=sub_alphas,
            transformation=submesh_transform,
            # With shared points, all submeshes share the same welded point
            # array, so the crease pairs (welded point indices) are valid for
            # each of them
            crease_pairs=sub_creases,
            crease_weights=sub_crease_weights,
            normals_pretransformed=normals_pretransformed,
            mat=mat,
            # Unique slot id per submesh (material x island group); starts at 1
            # because tri AOV layer 2 is also read by the wireframe texture,
            # which skips an edge class when the value is 0
            slot=g + 1,
        ))

    _stage('payloads', _t)
    duration = time() - start_time
    if _stage_t is not None:
        print(f"[BLC-STAGES] {mesh_key}: " + " ".join(f"{k}={v:.3f}" for k, v in _stage_t.items()), flush=True)
    info = dict(duration=duration, num_points=num_points,
                num_raw=len(vertex_points))
    return payloads, info


def define_submeshes(luxcore_scene, payloads):
    """Define the computed submeshes in the LuxCore scene.

    Must run in the main thread (the LuxCore scene is not thread-safe).
    Returns the ExportedMesh with the per-submesh material definitions.
    """
    mesh_definitions = []
    with _SCENE_LOCK:
        for i, payload in enumerate(payloads):
            luxcore_scene.DefineMeshExt(
                name=payload["name"],
                points=payload["points"],
                triangles=payload["triangles"],
                normals=payload["normals"],
                uvs=payload["uvs"],
                colors=payload["colors"],
                alphas=payload["alphas"],
                transformation=payload["transformation"],
                # All submeshes share the same welded point array, so the
                # crease pairs (welded point indices) are identical for all
                # of them: set them only on the first submesh. The subdiv
                # envelope builder does not read per-submesh creases, and a
                # single-submesh object is its own first submesh.
                crease_pairs=payload["crease_pairs"] if i == 0 else None,
                crease_weights=payload["crease_weights"] if i == 0 else None,
                normals_pretransformed=payload.get("normals_pretransformed", False),
            )
            luxcore_scene.SetMeshTriangleAOV(
                payload["name"], MATERIAL_TRI_AOV_INDEX,
                np.full(len(payload["triangles"]), payload["slot"], dtype=np.float32),
            )
            mesh_definitions.append((payload["name"], payload["mat"], payload["slot"]))

    # Per-face material slot, consumed by the C++ subdiv envelope builder
    # (MATERIAL_TRI_AOV_INDEX in LuxCore) to split the subdivided result
    # back per material
    return caches.exported_data.ExportedMesh(mesh_definitions)


def convert(
    obj,
    mesh_key,
    depsgraph,
    luxcore_scene,
    is_viewport_render,
    use_instancing,
    transform,
    exporter=None,
    share_points=True,
):
    """Convert one object: extract (main thread), compute, define."""
    start_time = time()

    data = extract_mesh_data(obj, depsgraph)
    if data is None:
        return None

    payloads, info = compute_submeshes(
        data, mesh_key, transform, is_viewport_render, use_instancing,
        share_points=share_points,
    )

    duration = time() - start_time
    if exporter and exporter.stats:
        exporter.stats.export_time_meshes.value += duration
    print(f"[BLC] Export duration: {duration:.3f}s")
    print("[BLC]")

    return define_submeshes(luxcore_scene, payloads)


def convert_objects(jobs, depsgraph, luxcore_scene, exporter=None,
                    max_workers=None):
    """Batch-convert several objects in parallel.

    jobs: list of (obj, mesh_key, transform, is_viewport_render, use_instancing).
    Extraction (Blender API) runs serially in the calling thread, the compute
    phase (weld, islands, gathers) runs in a thread pool, and the LuxCore
    scene definition runs serially in the calling thread. A small window of
    objects is kept in flight to bound memory usage.
    Returns a list of ExportedMesh (or None), aligned with jobs.
    """
    if max_workers is None:
        max_workers = int(os.environ.get("BLC_EXPORT_WORKERS", "0")) or min(
            16, os.cpu_count() or 4
        )
    # How many objects may be extracted-but-not-yet-defined at once. This
    # bounds the memory held by in-flight extracted data + payloads, so scenes
    # with a few huge objects don't hold the whole scene's meshes at once.
    inflight_max = int(os.environ.get("BLC_EXPORT_INFLIGHT", "4"))

    results = [None] * len(jobs)
    debug = bool(os.environ.get("BLC_DEBUG_EXPORT"))

    def _compute(args):
        data, job = args
        if data is None:
            return None
        _obj, mesh_key, transform, is_viewport_render, use_instancing, share_points = job
        return compute_submeshes(
            data, mesh_key, transform, is_viewport_render, use_instancing,
            share_points=share_points,
        )

    def _define(result_index, comp):
        # Phase 3: define in the LuxCore scene, serially in the calling thread
        if comp is None:
            return
        payloads, info = comp
        results[result_index] = define_submeshes(luxcore_scene, payloads)
        if exporter and exporter.stats:
            exporter.stats.export_time_meshes.value += info["duration"]
        print(f"[BLC] Export duration: {info['duration']:.3f}s")
        print("[BLC]")

    # Pipeline with a window of inflight_max objects: while the pool computes
    # object i, the calling thread extracts object i+1 (extraction is
    # Blender-API bound and serial, compute overlaps it), then the oldest
    # object is defined in order.
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        pending = []  # (result_index, future)
        for i, job in enumerate(jobs):
            if debug:
                print(f"[BLC-DEBUG] extract {job[0].name}", flush=True)
            # Phase 1: extract, serially in the calling (main) thread
            data = extract_mesh_data(job[0], depsgraph)
            # Phase 2: submit compute to the pool
            pending.append((i, pool.submit(_compute, (data, job))))
            # Keep at most inflight_max objects in flight; define the oldest
            while len(pending) > inflight_max:
                ri, fut = pending.pop(0)
                if debug:
                    print(f"[BLC-DEBUG] object {ri} computed, defining", flush=True)
                _define(ri, fut.result())

        for ri, fut in pending:
            _define(ri, fut.result())

    return results

@contextmanager
def _prepare_mesh(obj, depsgraph):
    """
    Create a temporary mesh from an object.
    The mesh is guaranteed to be removed when the calling block ends.
    Can return None if no mesh could be created from the object (e.g. for empties)

    Use it like this:

    with mesh_converter.convert(obj, depsgraph) as mesh:
        if mesh:
            print(mesh.name)
            ...
    """

    mesh = None
    object_eval = None

    try:
        object_eval = obj.evaluated_get(depsgraph)
        if object_eval:
            mesh = object_eval.to_mesh()

            if mesh:
                # TODO test if this makes sense
                # has been tested briefly for_v2.10. Seems to work, also
                # including custom normals now
                ## but leaving this out on purpose because
                ## a) users should clean their meshes themselves, and
                ## b) this will allow some artistic effects
                # if object_eval.matrix_world.determinant() < 0.0:
                #     mesh.flip_normals()

                if not mesh.loop_triangles:
                    object_eval.to_mesh_clear()
                    mesh = None

            # No split_faces() here: in Blender 5.2 mesh.corner_normals already
            # honor sharp edges / smooth-by-angle (verified: default cube gets 3
            # distinct corner normals per vertex without splitting), and the
            # weld below merges any coincident vertices anyway (e.g. from
            # modifiers). Skipping split_faces avoids duplicating all vertices
            # of split meshes just to weld them back.

        yield mesh
    finally:
        if object_eval and mesh:
            object_eval.to_mesh_clear()
