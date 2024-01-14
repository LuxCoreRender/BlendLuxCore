import bpy
from contextlib import contextmanager
from time import time
from .caches.exported_data import ExportedMesh
from .. import utils
from ..utils.errorlog import LuxCoreErrorLog

def fast_custom_normals_supported():
    version = bpy.app.version
    if version == (2, 82, 7):
        return True
    if version[:2] == (2, 83):
        return True
    return False

def get_custom_normals_slow(mesh):
    if not mesh.has_custom_normals:
        return None

    custom_normals = [
        normal
        for loop_tri in mesh.loop_triangles
        for loop, split_normals in zip(loop_tri.loops, loop_tri.split_normals)
        for normal in split_normals
    ]

    return custom_normals

def convert(obj, mesh_key, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform, exporter=None):
    start_time = time()

    with _prepare_mesh(obj, depsgraph) as mesh:
        if mesh is None:
            return None

        custom_normals = None
        if mesh.has_custom_normals and not get_custom_normals_slow(mesh):
            start = time()
            custom_normals = fast_custom_normals_supported(mesh)
            elapsed = time() - start
            if elapsed > 0.3:
                LuxCoreErrorLog.add_warning(f"Slow custom normal export (took {elapsed:.1f} s)", obj_name=obj.name)

        loopTriPtr = mesh.loop_triangles[0].as_pointer()
        loopTriPolyPtr = mesh.loop_triangle_polygons[0].as_pointer()
        loopTriCount = len(mesh.loop_triangles)

        loopPtr = mesh.attributes.get('.corner_vert', mesh.loops).data[0].as_pointer()
        vertPtr = mesh.attributes.get('position', mesh.vertices).data[0].as_pointer()
        normalPtr = mesh.vertex_normals[0].as_pointer()

        loopUVsPtrList = [mesh.attributes.get(uv.name, uv.data).data[0].as_pointer() for uv in mesh.uv_layers] or [0]
        loopColsPtrList = [mesh.attributes.get(vcol.name, vcol.data).data[0].as_pointer() for vcol in mesh.vertex_colors] or [0]

        meshPtr = mesh.as_pointer()

        material_indices = [p.material_index for p in mesh.polygons]
        material_count = max(1, len(mesh.materials))

        mesh_transform = None if is_viewport_render or use_instancing else utils.matrix_to_list(transform)

        sharp_attr = 'sharp_face' in mesh.attributes
        sharpPtr = mesh.attributes['sharp_face'].data[0].as_pointer() if sharp_attr else 0

        mesh_definitions = luxcore_scene.DefineBlenderMesh(mesh_key, loopTriCount, loopTriPtr, loopTriPolyPtr, loopPtr,
                                                          vertPtr, normalPtr, sharpPtr, sharp_attr, loopUVsPtrList,
                                                          loopColsPtrList, meshPtr, material_count, mesh_transform,
                                                          bpy.app.version, material_indices, custom_normals)
        if exporter and exporter.stats:
            exporter.stats.export_time_meshes.value += time() - start_time

        return ExportedMesh(mesh_definitions)

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
                # If negative scaling, we have to invert the normals
                # if not mesh.has_custom_normals and object_eval.matrix_world.determinant() < 0.0:
                #     # Does not handle custom normals
                #     mesh.flip_normals()
                
                mesh.calc_loop_triangles()
                if not mesh.loop_triangles:
                    object_eval.to_mesh_clear()
                    mesh = None

            if mesh:
                if mesh.use_auto_smooth:
                    if not mesh.has_custom_normals:
                        mesh.calc_normals_split()
                    mesh.split_faces()
                
                mesh.calc_loop_triangles()
                
                if mesh.has_custom_normals:
                    mesh.calc_normals_split()

        yield mesh
    finally:
        if object_eval and mesh:
            object_eval.to_mesh_clear()
