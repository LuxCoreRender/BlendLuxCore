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


def fast_custom_normals_supported():
    version = bpy.app.version
    if version == (2, 82, 7):
        return True
    if version[:2] == (2, 83):
        return True
    return False


# https://blenderartists.org/t/\
# efficient-copying-of-vertex-coords-to-and-from-numpy-arrays/661467/2
def get_ndarray(
    bpy_collection: bpy.types.bpy_prop_collection,
    attr: str,
    stride: int,
    dtype: np.dtype,
):
    """Get a numpy array from a Blender collection."""
    count = len(bpy_collection)
    buffer = np.empty(shape=(count, stride), dtype=dtype)
    bpy_collection.foreach_get(attr, np.ravel(buffer))
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

        # Loop vertices
        loop_vertex_indices = get_ndarray(
            mesh.loops, "vertex_index", 1, np.uint32
        ).ravel()
        vertices = get_ndarray(mesh.vertices, "co", 3, np.float32)
        loop_vertices = vertices[loop_vertex_indices]

        # Loop triangles
        loop_triangles = get_ndarray(
            mesh.loop_triangles, "loops", 3, np.uint32
        )

        # Material slot index for each triangle
        loop_triangle_materials = get_ndarray(
            mesh.loop_triangles, "material_index", 1, np.uint32
        ).ravel()
        unique_mats = np.unique(loop_triangle_materials)

        # Normals
        loop_normals = get_ndarray(mesh.loops, "normal", 3, np.float32)

        # UV
        uvs = [
            get_ndarray(uv_layer.uv, "vector", 2, np.float32)
            for uv_layer in mesh.uv_layers
        ]

        # Colors
        rgba_colors = [
            get_ndarray(color_attribute.data, "color_srgb", 4, np.float32)
            for color_attribute in mesh.color_attributes
        ]
        rgb_colors = [rgba[:, :3] for rgba in rgba_colors]
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

        mesh_definitions = []
        for mat in unique_mats:
            mat_triangles = loop_triangles[loop_triangle_materials == mat]
            name = f"{str(mesh_key)}{mat:03d}"

            luxcore_scene.DefineMeshExt(
                name=name,
                points=loop_vertices,
                triangles=mat_triangles,
                normals=loop_normals,
                uvs=uvs,
                colors=rgb_colors,
                alphas=alphas,
                transformation=mesh_transform,
            )
            mesh_definitions.append((name, mat))

        if exporter and exporter.stats:
            exporter.stats.export_time_meshes.value += time() - start_time

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
