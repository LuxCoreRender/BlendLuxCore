import bpy
import numpy as np
from contextlib import contextmanager
from time import time
from .caches.exported_data import ExportedMesh
from .. import utils
from ..utils.errorlog import LuxCoreErrorLog

MIN_SUPPORTED_VERSION = (2, 83)
NORMALS_ELEMENT_SIZE = 3
NORMALS_ARRAY_SIZE = NORMALS_ELEMENT_SIZE * 3

def fast_custom_normals_supported():
    return bpy.app.version >= MIN_SUPPORTED_VERSION

def get_custom_normals_fast(mesh):
    if not mesh.has_custom_normals:
        return None

    loop_tri_count = len(mesh.loop_triangles)
    custom_normals = np.zeros((loop_tri_count, NORMALS_ARRAY_SIZE), dtype=np.float32)

    for i, loop_tri in enumerate(mesh.loop_triangles):
        split_normals = loop_tri.split_normals
        for j in range(NORMALS_ARRAY_SIZE):
            custom_normals[i, j] = split_normals[j // NORMALS_ELEMENT_SIZE][j % NORMALS_ELEMENT_SIZE]

    return custom_normals

def convert(obj, mesh_key, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform, exporter=None):
    start_time = time()
    
    with _prepare_mesh(obj, depsgraph) as mesh:
        if mesh is None:
            return None
        
        custom_normals = None
        if mesh.has_custom_normals and not fast_custom_normals_supported():
            start = time()
            custom_normals = get_custom_normals_fast(mesh)
            elapsed = time() - start
            if elapsed > 0.3:
                LuxCoreErrorLog.add_warning(
                    f"Slow custom normal export in this Blender version (took {elapsed:.1f} s)",
                    obj_name=obj.name
                )

        loop_tri_ptr = mesh.loop_triangles[0].as_pointer()
        loop_tri_poly_ptr = mesh.loop_triangle_polygons[0].as_pointer()
        loop_tri_count = len(mesh.loop_triangles)

        loop_ptr = (
            mesh.attributes['.corner_vert'].data[0].as_pointer()
            if '.corner_vert' in mesh.attributes
            else mesh.loops[0].as_pointer()
        )

        vert_ptr = (
            mesh.attributes['position'].data[0].as_pointer()
            if 'position' in mesh.attributes
            else mesh.vertices[0].as_pointer()
        )

        normal_ptr = mesh.vertex_normals[0].as_pointer()

        loop_uvs_ptr_list = [
            mesh.attributes[uv.name].data[0].as_pointer()
            if uv.name in mesh.attributes
            else uv.data[0].as_pointer()
            for uv in mesh.uv_layers
        ] if mesh.uv_layers else [0]

        loop_cols_ptr_list = [
            mesh.attributes[vcol.name].data[0].as_pointer()
            if vcol.name in mesh.attributes
            else vcol.data[0].as_pointer()
            for vcol in mesh.vertex_colors
        ] if mesh.vertex_colors else [0]

        mesh_ptr = mesh.as_pointer()

        material_indices = [p.material_index for p in mesh.polygons]
        material_count = max(1, len(mesh.materials))

        mesh_transform = (
            None
            if is_viewport_render or use_instancing
            else utils.matrix_to_list(transform)
        )

        sharp_attr = False
        sharp_ptr = 0

        if 'sharp_face' in mesh.attributes:
            sharp_attr = True
            sharp_ptr = mesh.attributes['sharp_face'].data[0].as_pointer()

        mesh_definitions = luxcore_scene.DefineBlenderMesh(
            mesh_key, loop_tri_count, loop_tri_ptr, loop_tri_poly_ptr, loop_ptr,
            vert_ptr, normal_ptr, sharp_ptr, sharp_attr, loop_uvs_ptr_list,
            loop_cols_ptr_list, mesh_ptr, material_count, mesh_transform,
            bpy.app.version, material_indices, custom_normals
        )
        
        if exporter and exporter.stats:
            exporter.stats.export_time_meshes.value += time() - start_time

        return ExportedMesh(mesh_definitions)

@contextmanager
def _prepare_mesh(obj, depsgraph):
    mesh = None
    object_eval = None

    try:
        object_eval = obj.evaluated_get(depsgraph)
        if object_eval:
            mesh = object_eval.to_mesh()

            if mesh:
                mesh.calc_loop_triangles()
                if not mesh.loop_triangles:
                    object_eval.to_mesh_clear()
                    mesh = None

            if mesh:
                if bpy.app.version > (3, 9, 9):
                    if 'sharp_face' in mesh.attributes:
                        mesh.split_faces()
                else:
                    if mesh.use_auto_smooth:
                        if not mesh.has_custom_normals:
                            mesh.calc_normals()
                        mesh.split_faces()

                    mesh.calc_loop_triangles()

                    if mesh.has_custom_normals:
                        mesh.calc_normals_split()

        yield mesh
    finally:
        if object_eval and mesh:
            object_eval.to_mesh_clear()
