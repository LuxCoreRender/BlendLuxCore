import bpy
from contextlib import contextmanager
from time import time
from .caches.exported_data import ExportedMesh
from .. import utils
from ..utils.errorlog import LuxCoreErrorLog


def fast_custom_normals_supported():
    return bpy.app.version >= (2, 83)

def get_custom_normals_slow(mesh):
    if not mesh.has_custom_normals:
        return None

    custom_normals = [value for loop_tri in mesh.loop_triangles for split_normals in loop_tri.split_normals for value in split_normals]

    return custom_normals

def convert(obj, mesh_key, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform, exporter=None):
    start_time = time()

    # Use Local Variables
    mesh_attributes = obj.data.attributes
    mesh_uv_layers = obj.data.uv_layers
    mesh_vertex_colors = obj.data.vertex_colors

    # Mesh Preparation
    with _prepare_mesh(obj, depsgraph) as mesh:
        if mesh is None:
            return None

        custom_normals = None
        if mesh.has_custom_normals and not fast_custom_normals_supported():
            start = time()
            custom_normals = get_custom_normals_slow(mesh)
            elapsed = time() - start
            if elapsed > 0.3:
                LuxCoreErrorLog.add_warning("Slow custom normal export in this Blender version (took %.1f s)" % elapsed, obj_name=obj.name)

        # Avoid Repeated Data Access
        loop_count = len(mesh.loop_triangles)
        polygon_material_indices = [p.material_index for p in mesh.polygons]
        material_count = max(1, len(mesh.materials))

        # Minimize Dictionary Lookups
        position_attr = mesh_attributes.get('position')

        loopTriPtr = mesh.loop_triangles[0].as_pointer()
        loopTriPolyPtr = mesh.loop_triangle_polygons[0].as_pointer()
        loopTriCount = loop_count

        if '.corner_vert' in mesh_attributes:
            loopPtr = mesh_attributes['.corner_vert'].data[0].as_pointer()
        else:
            loopPtr = mesh.loops[0].as_pointer()

        if 'position' in mesh_attributes:
            vertPtr = position_attr.data[0].as_pointer()
        else:
            vertPtr = mesh.vertices[0].as_pointer()

        normalPtr = mesh.vertex_normals[0].as_pointer()

        loopUVsPtrList = [mesh_attributes[uv.name].data[0].as_pointer() if uv.name in mesh_attributes else uv.data[0].as_pointer() for uv in mesh_uv_layers]
        loopColsPtrList = [mesh_attributes[vcol.name].data[0].as_pointer() if vcol.name in mesh_attributes else vcol.data[0].as_pointer() for vcol in mesh_vertex_colors]

        meshPtr = mesh.as_pointer()

        if 'sharp_face' in mesh_attributes:
            sharp_attr = True
            sharpPtr = mesh_attributes['sharp_face'].data[0].as_pointer()
        else:
            sharp_attr = False
            sharpPtr = 0

        # Reduce Redundant Checks
        mesh_transform = None if is_viewport_render or use_instancing else utils.matrix_to_list(transform)

        mesh_definitions = luxcore_scene.DefineBlenderMesh(mesh_key, loopTriCount, loopTriPtr, loopTriPolyPtr, loopPtr,
                                                          vertPtr, normalPtr, sharpPtr, sharp_attr, loopUVsPtrList,
                                                          loopColsPtrList, meshPtr, material_count, mesh_transform,
                                                          bpy.app.version, polygon_material_indices, custom_normals)
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

            # Inside the _prepare_mesh function
            if mesh:
                if bpy.app.version > (3, 9, 9):
                    if 'sharp_face' in mesh.attributes:
                        mesh.split_faces()
                else:
                    if mesh.use_auto_smooth:
                        if not mesh.has_custom_normals:
                            mesh.create_normals_split()  # Updated line
                        mesh.split_faces()

                    mesh.calc_loop_triangles()

                    if mesh.has_custom_normals:
                        mesh.calc_normals_split_custom()  # Updated line


        yield mesh
    finally:
        if object_eval and mesh:
            object_eval.to_mesh_clear()
