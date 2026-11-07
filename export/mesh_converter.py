from contextlib import contextmanager
from time import time
import numpy as np

_needs_reload = "bpy" in locals()

import bpy

from . import caches
from .. import utils
from ..utils.errorlog import LuxCoreErrorLog

if _needs_reload:
    import importlib

    importlib.reload(caches)
    importlib.reload(utils)


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
    start_time = time()

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

        # Points: weld coincident vertices (the evaluated mesh may contain
        # split vertices, e.g. from split_faces() at sharp edges). Coincident
        # vertices must not stay distinct, otherwise modifiers displacing
        # vertices (like subdivision) would open gaps in the mesh.
        # Discontinuities of varying data (uv...) are handled by submeshes
        # (see UV islands below), not by split vertices.
        # The welded point array is shared by all the submeshes defined below
        # (LuxCore shares the point storage between meshes defined with
        # identical points).
        vertex_points = get_ndarray(mesh.vertices, "co", 3, np.float32)
        welded_points, first_index, weld_inverse = np.unique(
            vertex_points, axis=0, return_index=True, return_inverse=True
        )
        num_points = len(welded_points)

        # Per-vertex data of the (possibly split) source vertices
        vertex_normals = get_ndarray(mesh.vertices, "normal", 3, np.float32)

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
        # Per-loop UV signature (all layers), used to detect UV seams
        if loop_uvs:
            uv_sig = np.stack(loop_uvs, axis=1)  # [n_loops, n_layers, 2]
        else:
            uv_sig = np.zeros((len(loop_vertices), 0, 2), dtype=np.float32)

        # Vertex color attributes
        color_attrs = [
            (
                get_ndarray(attribute.data, "color", 4, np.float32),
                attribute.domain,
            )
            for attribute in mesh.color_attributes
        ]

        # --- UV islands ------------------------------------------------------
        # Union-find over loops: the two loops at the endpoints of a shared
        # edge belong to the same island when their UVs match on every UV
        # layer. A loop thus belongs to the island of its (vertex, uv) pair;
        # a triangle goes to the island of its first loop. Triangles of
        # different islands (or materials) are exported as separate submeshes,
        # so that each submesh has consistent per-vertex UVs over the shared
        # welded points.
        loop_welded = weld_inverse[loop_vertices]
        n_tris = len(triangle_loops)
        n_loops = len(loop_vertices)

        parent = np.arange(n_loops)

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        # edge (welded endpoints, sorted) -> [(loop index, uv at min, uv at max)]
        edge_map = {}
        for t in range(n_tris):
            loops = triangle_loops[t]
            w = loop_welded[loops]
            # The 3 loops of a triangle belong to the same UV patch (a seam
            # cannot run through the interior of a triangle)
            for k in range(1, 3):
                r1, r2 = find(int(loops[0])), find(int(loops[k]))
                if r1 != r2:
                    parent[r1] = r2
            for k in range(3):
                la, lb = int(loops[k]), int(loops[(k + 1) % 3])
                a, b = int(w[k]), int(w[(k + 1) % 3])
                ua = uv_sig[la].tobytes()
                ub = uv_sig[lb].tobytes()
                if a > b:
                    a, b, la, lb, ua, ub = b, a, lb, la, ub, ua
                edge_map.setdefault((a, b), []).append((la, lb, ua, ub))
        for lst in edge_map.values():
            if len(lst) == 2:
                (la1, lb1, ua1, ub1), (la2, lb2, ua2, ub2) = lst
                # same edge endpoints: union when the UVs match at both ends
                if ua1 == ua2 and ub1 == ub2:
                    r1, r2 = find(la1), find(la2)
                    if r1 != r2:
                        parent[r1] = r2
                    r1, r2 = find(lb1), find(lb2)
                    if r1 != r2:
                        parent[r1] = r2

        loop_island = np.array([find(l) for l in range(n_loops)])
        # Compact island numbering (used in submesh names)
        _, loop_island = np.unique(loop_island, return_inverse=True)
        # Triangle island = island of its first loop
        island = loop_island[triangle_loops[:, 0]] if n_tris else np.zeros(0, dtype=np.int64)
        n_islands = int(loop_island.max()) + 1 if n_loops else 1

        # Group triangles by (material, island)
        tri_keys = loop_triangle_materials * n_islands + island
        group_keys, tri_group = np.unique(tri_keys, return_inverse=True)
        groups = {}
        for t in range(n_tris):
            groups.setdefault(int(tri_group[t]), []).append(t)

        # Transformation
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

        mesh_definitions = []
        first_name = None
        for gkey in sorted(groups.keys()):
            mat = gkey // n_islands
            isl = gkey % n_islands
            g_tris = np.array(groups[gkey], dtype=np.int64)
            g_loops = triangle_loops[g_tris]       # [g, 3] loop indices
            g_loop_flat = g_loops.ravel()
            gw = loop_welded[g_loops]              # welded vertex per corner
            # Remap the triangle loop indices to welded vertex indices, so
            # that all the submeshes index the same shared welded point array
            # (uint32, as expected by pyluxcore)
            sub_triangles = gw.astype(np.uint32)
            name = f"{str(mesh_key)}{mat:03d}i{isl:03d}"

            # Loops of this submesh that belong to this island (a triangle
            # corner at a seam vertex may belong to another island)
            isl_mask = loop_island[g_loop_flat] == isl
            isl_loops = g_loop_flat[isl_mask]
            isl_gw = gw.ravel()[isl_mask]

            # Per-submesh varying data, gathered from this island's loops
            # (consistent within the island by construction), aligned with
            # the shared welded points
            sub_uvs = []
            for loop_uv in loop_uvs:
                uv_sub = np.zeros((num_points, 2), dtype=np.float32)
                uv_sub[isl_gw] = loop_uv[isl_loops]
                sub_uvs.append(uv_sub)
            sub_normals = np.zeros((num_points, 3), dtype=np.float32)
            sub_normals[isl_gw] = vertex_normals[loop_vertices[isl_loops]]
            sub_rgb, sub_alphas = [], []
            for colors, domain in color_attrs:
                if domain == "POINT":
                    rgba = colors[first_index]
                elif domain == "CORNER":
                    rgba = np.zeros((num_points, 4), dtype=np.float32)
                    rgba[isl_gw] = colors[isl_loops]
                else:
                    raise ValueError(f"Unhandled attribute domain: '{domain}'")
                sub_rgb.append(rgba[:, :3])
                sub_alphas.append(rgba[:, 3])

            if first_name is None:
                # First submesh: send the points (and bake the transformation
                # into them, if any)
                points = welded_points
                submesh_transform = mesh_transform
                first_name = name
            else:
                # Other submeshes: share the point buffer of the first submesh
                # (by name) instead of re-sending the same points. The
                # transformation is already baked into those shared points.
                points = first_name
                submesh_transform = None

            print(f"[BLC] - Submesh {name}: {len(sub_triangles)} triangles")

            luxcore_scene.DefineMeshExt(
                name=name,
                points=points,
                triangles=sub_triangles,
                normals=sub_normals,
                uvs=sub_uvs,
                colors=sub_rgb,
                alphas=sub_alphas,
                transformation=submesh_transform,
            )
            mesh_definitions.append((name, mat))

        duration = time() - start_time
        if exporter and exporter.stats:
            exporter.stats.export_time_meshes.value += duration
        print(f"[BLC] Export duration: {duration:.3f}s")
        print("[BLC]")

        return caches.exported_data.ExportedMesh(mesh_definitions)


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

            # TODO implement new normals handling
            if mesh:
                mesh.split_faces()  # Applies smooth by angle operator

        yield mesh
    finally:
        if object_eval and mesh:
            object_eval.to_mesh_clear()
