# Copyright (C) 2025 AUTHORS

# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, version 3.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

"""Conversion of Blender mesh objects into LuxCore scene meshes.

Entry points (called from export/__init__.py via the object cache):

- convert(): convert a single object, serially (viewport / live-update path).
- convert_objects(): batch entry point of the render-export pre-pass. Takes a
  list of jobs (obj, mesh_key, transform, is_viewport_render, use_instancing);
  returns a list of ExportedMesh aligned with the jobs.

Both run the same 3-phase pipeline per object:

1. extract_mesh_data() -- Blender API -> numpy arrays. Must run in the main
   thread (Blender data is not thread-safe); this is why convert_objects()
   extracts serially in the calling thread and only parallelizes phases 2+3.
2. compute_submeshes() -- the C++/TBB implementation in pyluxcore
   (compute_submeshes_c, GIL released): weld coincident points, split into
   varying-data islands (union-find over shared edges with matching UV/normal
   signatures, small-island merge), group triangles by (material, island) and
   gather the per-submesh payloads (points, triangles, normals, UV/color/alpha
   layers, creases, optional baked transform). All submeshes of an object
   always share one welded point buffer (the root mesh): the C++ subdivision
   envelope and all shape modifiers (merge on distance, displacement, ...)
   rely on seeing the whole object's points.
3. define_submeshes() -- build and insert the meshes into the LuxCore scene,
   batched via Scene.DefineMeshesExt when available (one GIL release + one
   mesh-def mutex acquisition per object), else one DefineMeshExt per submesh.
   The material slot of each triangle is passed as the constant triangle AOV
   MATERIAL_TRI_AOV_INDEX, which the C++ subdiv envelope builder reads to
   split the subdivided result back per material.

Threading model: convert_objects() runs phases 2+3 in a ThreadPoolExecutor of
DEFAULT_EXPORT_WORKERS threads (BLC_EXPORT_WORKERS overrides), keeping a
window of at most BLC_EXPORT_INFLIGHT extracted-but-not-yet-converted objects
(default: the pool size) to bound peak memory. pyluxcore serializes the scene
mesh mutations internally (mesh-def mutex) and releases the GIL around the
C++ work, so worker threads are safe. Per-mesh log lines are buffered and
printed by the main thread so they stay grouped by mesh.

Other knobs: BLC_DEBUG_EXPORT=1, BLC_DEBUG_MESH=1,
BLC_TIME_STAGES=1 (per-stage timings in the log).
"""

import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from time import time
import numpy as np

_needs_reload = "bpy" in locals()

import bpy
import pyluxcore

from . import caches
from .. import utils
from ..utils import node as utils_node
from ..utils.log import log, log_str


def object_uses_subdiv(obj):
    """True if any material of the object has a subdiv shape node."""
    for mat_slot in obj.material_slots:
        mat = mat_slot.material
        if mat and mat.luxcore.node_tree and utils_node.has_nodes_multi(
            mat.luxcore.node_tree, {"LuxCoreNodeShapeSubdiv"}, True
        ):
            return True
    return False


def node_tree_has_shape_nodes(node_tree):
    """True if the node tree contains any shape node (also in pointers)."""
    if node_tree is None:
        return False
    for node in node_tree.nodes:
        if node.bl_idname.startswith("LuxCoreNodeShape"):
            return True
        if node.bl_idname == "LuxCoreNodeTreePointer" and node.node_tree:
            try:
                if node_tree_has_shape_nodes(node.node_tree):
                    return True
            except RecursionError:
                return False
    return False

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

# Default size of the mesh pre-pass thread pool. A fixed constant, not
# os.cpu_count(), so export behaves identically on every machine. The compute
# phase releases the GIL and TBB parallelizes its inner loops; the pool's
# job is to overlap the serial parts (Blender-API extraction, scene insertion
# under pyluxcore's mesh mutex) with other objects' compute. HallBench
# pre-pass wall: 3.5s at 4 workers, 2.8s at 8 (+120MB peak RSS), 2.6s at 16
# (+400MB) -- 8 is the knee. Override with BLC_EXPORT_WORKERS.
DEFAULT_EXPORT_WORKERS = 8


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

    dtype is critical: foreach_get only writes the buffer directly when the
    numpy dtype matches the RNA property's raw type exactly (see
    foreach_compat_buffer in Blender's bpy_rna.cc): 'f' for PROP_FLOAT,
    'i' for signed PROP_INT, 'I' for PROP_UNSIGNED int, etc. On mismatch it
    silently falls back to a per-element Python loop, which is >100x slower
    on large meshes. Unsigned index props (vertex_index, loops, vertices,
    material_index) therefore need uint32, not int32.
    """
    count = len(bpy_collection)
    buffer = np.empty(shape=(count, stride if stride else 1), dtype=dtype)
    bpy_collection.foreach_get(attr, np.ravel(buffer))
    if not stride:
        buffer = buffer.ravel()
    return buffer


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
            # "vertices" is PROP_UNSIGNED: uint32 buffer keeps foreach_get on
            # the raw buffer path (int32 silently drops to the slow per-element
            # fallback). compute_submeshes_c forcecasts to int32 on its side.
            edge_verts = get_ndarray(mesh.edges, "vertices", 2, np.uint32)
            edge_crease = get_ndarray(crease_attr.data, "value", 0, np.float32)
        vert_crease_attr = mesh.attributes.get("crease_vert")
        if (
            vert_crease_attr is not None
            and vert_crease_attr.domain == "POINT"
            and np.any(get_ndarray(vert_crease_attr.data, "value", 0, np.float32) > 0.0)
        ):
            log(
                "Warning: vertex creases (crease_vert) are not exported "
                "(OpenSubdiv topology descriptors only support edge creases)"
            )

        return {
            "loop_vertices": loop_vertices,
            "vertex_points": vertex_points,
            "vertex_normals": vertex_normals,
            "loop_normals": loop_normals,
            "triangle_loops": triangle_loops,
            "loop_triangle_materials": loop_triangle_materials,
            "loop_uvs": loop_uvs,
            "color_attrs": color_attrs,
            "edge_verts": edge_verts,
            "edge_crease": edge_crease,
        }


_compute_submeshes_c = getattr(pyluxcore, "compute_submeshes_c", None)

# DefineMeshExt can set a constant per-triangle AOV itself (tri_aov_index /
# tri_aov_value, added to pyluxcore): avoids a separate SetMeshTriangleAOV
# round-trip per submesh (numpy alloc + GIL-held copy + mesh-def mutex)
_DEFINE_EXT_HAS_TRI_AOV = "tri_aov_index" in (pyluxcore.Scene.DefineMeshExt.__doc__ or "")
# Batch define (one GIL release + one mesh-def lock for all submeshes of an
# object, instead of one pybind call per submesh)
_DEFINE_MESHES_EXT = hasattr(pyluxcore.Scene, "DefineMeshesExt")


def compute_submeshes(data, mesh_key, transform, is_viewport_render, use_instancing,
                      log_lines=None, shape_name=None):
    """Weld points, find varying-data islands, group triangles by
    (material, island) and gather the per-submesh varying data, using the
    C++/TBB implementation in pyluxcore. Returns (payloads, info):
    payloads is a list of dicts ready for define_submeshes(), info holds
    log/stat data.

    log_lines: when a list is passed, log messages are appended to it instead
    of being printed. The parallel exporter uses this to print the messages
    of each mesh from the main thread, so they stay grouped by mesh.

    """
    if _compute_submeshes_c is None:
        raise RuntimeError(
            "pyluxcore.compute_submeshes_c is not available in this pyluxcore build"
        )
    if log_lines is None:
        def emit(msg):
            log(msg)
    else:
        def emit(msg):
            log_lines.append(log_str(msg))
    # Pass the transform only when it will be applied (not in viewport,
    # not instanced)
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
        True,  # share_points: submeshes always share the root point buffer
        str(mesh_key),
    )
    if shape_name is not None:
        # Group all submeshes of this object into one LuxCore Shape handle
        # (named shape_name) sharing the root point buffer
        for payload in payloads:
            payload["submesh_name"] = shape_name
    emit(f"Exporting '{str(mesh_key)}' - {len(payloads)} submesh(es)")
    emit(f"- {info['num_points']} welded points (shared between submeshes), "
         f"from {info['num_raw']} raw vertices")
    emit(f"- {len(data['loop_uvs'])} uv layer(s)" if len(data['loop_uvs']) != 1
         else "- 1 uv layer")
    emit(f"- {len(data['color_attrs'])} color layer(s)" if len(data['color_attrs']) != 1
         else "- 1 color layer")
    if os.environ.get("BLC_TIME_STAGES"):
        st = info.get("stages", {})
        emit("[BLC-STAGES] " + str(mesh_key) + ": " +
             " ".join(f"{k}={v:.3f}" for k, v in st.items()))
    return payloads, info


def define_submeshes(luxcore_scene, payloads):
    """Define the computed submeshes in the LuxCore scene.

    Safe to call from worker threads: pyluxcore serializes the scene mesh
    mutations internally (and releases the GIL around the C++ calls).
    Returns the ExportedMesh with the per-submesh material definitions.
    """
    mesh_definitions = []
    if _DEFINE_MESHES_EXT:
        # Batch path: all submeshes of this object defined in one C++ call
        batch = []
        for i, payload in enumerate(payloads):
            # All submeshes share the same welded point array, so the
            # crease pairs (welded point indices) are identical for all
            # of them: set them only on the first submesh. The subdiv
            # envelope builder does not read per-submesh creases, and a
            # single-submesh object is its own first submesh.
            # The payload dicts are ours (built by compute_submeshes), so
            # mutate them in place instead of copying each one.
            if i != 0:
                payload["crease_pairs"] = None
                payload["crease_weights"] = None
            if _DEFINE_EXT_HAS_TRI_AOV:
                payload["tri_aov_index"] = MATERIAL_TRI_AOV_INDEX
                payload["tri_aov_value"] = float(payload["slot"])
            batch.append(payload)
        luxcore_scene.DefineMeshesExt(batch)
        for payload in payloads:
            mesh_definitions.append((payload["name"], payload["mat"], payload["slot"]))
        return caches.exported_data.ExportedMesh(mesh_definitions)
    for i, payload in enumerate(payloads):
        extra = {}
        if _DEFINE_EXT_HAS_TRI_AOV:
            # Set the material-slot AOV inside DefineMeshExt (no extra
            # pybind round-trip / GIL-held array copy per submesh)
            extra["tri_aov_index"] = MATERIAL_TRI_AOV_INDEX
            extra["tri_aov_value"] = float(payload["slot"])
        luxcore_scene.DefineMeshExt(
            name=payload["name"],
            submesh_name=payload.get("submesh_name"),
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
            **extra,
        )
        if not _DEFINE_EXT_HAS_TRI_AOV:
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
):
    """Convert one object: extract (main thread), compute, define."""
    start_time = time()

    if (data := extract_mesh_data(obj, depsgraph)) is None:
        return None

    # Group the submeshes into one Shape (named after the mesh key) unless a
    # material uses subdiv (subdiv keeps per-submesh shapes for the matslot
    # resplit)
    shape_name = None if object_uses_subdiv(obj) else str(mesh_key)
    payloads, _info = compute_submeshes(
        data, mesh_key, transform, is_viewport_render, use_instancing,
        shape_name=shape_name,
    )

    duration = time() - start_time
    if exporter and exporter.stats:
        exporter.stats.export_time_meshes.value += duration
    log(f"Export duration: {duration:.3f}s")
    log("")

    return define_submeshes(luxcore_scene, payloads)


def convert_objects(jobs, depsgraph, luxcore_scene, exporter=None,
                    max_workers=None):
    """Batch-convert several objects in parallel.

    jobs: list of (obj, mesh_key, transform, is_viewport_render, use_instancing).
    Extraction (Blender API) runs serially in the calling thread; the compute
    phase (weld, islands, gathers) and the LuxCore scene definition are fused
    and run in a thread pool (pyluxcore serializes the scene mesh mutations
    internally and releases the GIL around the C++ calls). A small window of
    objects is kept in flight to bound memory usage.
    Returns a list of ExportedMesh (or None), aligned with jobs.
    """
    if max_workers is None:
        max_workers = (
            int(os.environ.get("BLC_EXPORT_WORKERS", "0")) or DEFAULT_EXPORT_WORKERS
        )
    # Window of extracted-but-not-yet-converted objects. The window caps
    # parallelism at its own size, so it must be at least the pool size or
    # the pool starves; it also bounds the memory held by in-flight extracted
    # data + payloads (scenes with a few huge objects never hold the whole
    # scene's meshes at once). Defaults to 3x the pool size: extraction is
    # serial in the calling thread, so a larger window keeps the pool busy
    # while the next object is being extracted (measured knee: CannelleEtFromage
    # pre-pass 2.09s -> 1.65s, HallBench 2.72s -> 2.29s at 8 workers / 24
    # inflight). Override with BLC_EXPORT_INFLIGHT.
    inflight_max = (
        int(os.environ.get("BLC_EXPORT_INFLIGHT", "0")) or 3 * max_workers
    )

    results = [None] * len(jobs)
    debug = bool(os.environ.get("BLC_DEBUG_EXPORT"))

    def _compute_and_define(args):
        # Phases 2+3, fused in the worker: compute the submeshes, then define
        # them in the LuxCore scene (thread-safe in pyluxcore)
        data, job = args
        if data is None:
            return None
        mesh_key, transform, is_viewport_render, use_instancing = job[1:]
        # Buffer this mesh's log messages: they are printed by the main
        # thread in _collect, so the lines of each mesh stay grouped together
        log_lines = []
        shape_name = None if object_uses_subdiv(job[0]) else str(mesh_key)
        payloads, info = compute_submeshes(
            data, mesh_key, transform, is_viewport_render, use_instancing,
            log_lines=log_lines, shape_name=shape_name,
        )
        result = define_submeshes(luxcore_scene, payloads)
        return result, info, log_lines

    def _collect(result_index, fut):
        if (comp := fut.result()) is None:
            return
        results[result_index], info, log_lines = comp
        if exporter and exporter.stats:
            exporter.stats.export_time_meshes.value += info["duration"]
        for line in log_lines:
            print(line)
        log(f"Export duration: {info['duration']:.3f}s")
        log("")

    # Pipeline with a window of inflight_max objects: while the pool converts
    # object i (compute + define), the calling thread extracts object i+1
    # (extraction is Blender-API bound and serial, so it overlaps the pool),
    # then the oldest object's future is collected.
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        pending = []  # (result_index, future)
        for i, job in enumerate(jobs):
            if debug:
                print(f"[BLC-DEBUG] extract {job[0].name}", flush=True)
            # Phase 1: extract, serially in the calling (main) thread
            data = extract_mesh_data(job[0], depsgraph)
            # Phases 2+3: submit compute+define to the pool
            pending.append((i, pool.submit(_compute_and_define, (data, job))))
            # Keep at most inflight_max objects in flight; collect the oldest
            while len(pending) > inflight_max:
                ri, fut = pending.pop(0)
                if debug:
                    print(f"[BLC-DEBUG] object {ri} converted", flush=True)
                _collect(ri, fut)

        for ri, fut in pending:
            _collect(ri, fut)

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
        if (object_eval := obj.evaluated_get(depsgraph)):
            if mesh := object_eval.to_mesh():
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
