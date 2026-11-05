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

        # Points: the unique mesh vertices. The same array is shared by all
        # the submeshes defined below (LuxCore shares the point storage
        # between meshes defined with identical points)
        vertex_points = get_ndarray(mesh.vertices, "co", 3, np.float32)
        num_vertices = len(vertex_points)

        # Normals (per-vertex)
        vertex_normals = get_ndarray(mesh.vertices, "normal", 3, np.float32)

        # Gather per-loop data (uv, corner colors...) into per-vertex arrays,
        # so that they stay aligned with the unique points. When several
        # loops of a same vertex disagree (e.g. UV seams), the last loop wins.
        def gather_per_vertex(loop_data):
            per_vertex = np.zeros(
                (num_vertices,) + loop_data.shape[1:], dtype=loop_data.dtype
            )
            per_vertex[loop_vertices] = loop_data
            return per_vertex

        # Triangle loop indices
        triangle_loops = get_ndarray(
            mesh.loop_triangles, "loops", 3, np.uint32
        )

        # Material slot index for each triangle
        loop_triangle_materials = get_ndarray(
            mesh.loop_triangles, "material_index", 1, np.uint32
        ).ravel()
        unique_mats = np.unique(loop_triangle_materials)

        # UV (per-loop in Blender, gathered per-vertex)
        uvs = [
            gather_per_vertex(get_ndarray(uv_layer.uv, "vector", 2, np.float32))
            for uv_layer in mesh.uv_layers
        ]

        # Vertex colors
        def reshape_colors(colors, domain):
            if domain == "POINT":
                return colors
            elif domain == "CORNER":
                return gather_per_vertex(colors)
            else:
                raise ValueError(f"Unhandled attribute domain: '{domain}'")

        rgba_colors = [
            reshape_colors(
                get_ndarray(attribute.data, "color", 4, np.float32),
                attribute.domain,
            )
            for attribute in mesh.color_attributes
        ]
        rgb = [rgba[:, :3] for rgba in rgba_colors]
        alphas = [rgba[:, 3] for rgba in rgba_colors]

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
        print(f"[BLC] Exporting '{str(mesh_key)}' - {len(unique_mats)} submesh(es)")
        print(f"[BLC] - {num_vertices} points (shared between submeshes)")
        print(f"[BLC] - {len(vertex_normals)} normals")
        print(f"[BLC] - {fmt_layer(uvs, 'uv')}")
        print(f"[BLC] - {fmt_layer(rgb, 'color')}")
        print(f"[BLC] - {fmt_layer(alphas, 'alpha')}")

        mesh_definitions = []
        for idx, mat in enumerate(unique_mats):
            # Remap the triangle loop indices to vertex indices, so that all
            # the submeshes index the same shared unique point array
            mat_triangles = loop_vertices[triangle_loops[loop_triangle_materials == mat]]
            name = f"{str(mesh_key)}{mat:03d}"

            if idx == 0:
                # First submesh: send the points (and bake the transformation
                # into them, if any)
                points = vertex_points
                submesh_transform = mesh_transform
            else:
                # Other submeshes: share the point buffer of the first submesh
                # (by name) instead of re-sending the same points. The
                # transformation is already baked into those shared points.
                points = mesh_definitions[0][0]
                submesh_transform = None

            print(f"[BLC] - Submesh #{mat:03d}: {len(mat_triangles)} triangles")

            luxcore_scene.DefineMeshExt(
                name=name,
                points=points,
                triangles=mat_triangles,
                normals=vertex_normals,
                uvs=uvs,
                colors=rgb,
                alphas=alphas,
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
