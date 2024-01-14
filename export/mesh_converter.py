import bpy
from contextlib import contextmanager
from time import time
from .caches.exported_data import ExportedMesh
from .. import utils
from ..utils.errorlog import LuxCoreErrorLog

def get_custom_normals_slow(mesh):
    """
    Slow fallback that reads custom normals via Python, used if fast
    custom normal reading via C++ is not supported for this Blender version
    """

    if not mesh.has_custom_normals:
        return None

    # Flat list of 3-element normal vectors
    custom_normals = [0] * (len(mesh.loops) * 3)

    for loop_tri in mesh.loop_triangles:
        loops = loop_tri.loops
        split_normals = loop_tri.split_normals

        start = loops[0] * 3
        custom_normals[start:start + 3] = split_normals[0][:]
        start = loops[1] * 3
        custom_normals[start:start + 3] = split_normals[1][:]
        start = loops[2] * 3
        custom_normals[start:start + 3] = split_normals[2][:]

    return custom_normals


def convert(obj, mesh_key, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform, exporter=None):
    start_time = time()
    
    with _prepare_mesh(obj, depsgraph) as mesh:
        if mesh is None:
            return None

        custom_normals = None
        mesh.calc_normals_split()
        if mesh.has_custom_normals:
            start = time()
            custom_normals = get_custom_normals_slow(mesh)
            elapsed = time() - start

            if elapsed > 0.3:
                LuxCoreErrorLog.add_warning("Slow custom normal export in this Blender version (took %.1f s)"
                                            % elapsed, obj_name=obj.name)

        loopTriPtr = mesh.loop_triangles[0].as_pointer()
        loopTriPolyPtr = mesh.loop_triangle_polygons[0].as_pointer()
        loopTriCount = len(mesh.loop_triangles)

        if '.corner_vert' in mesh.attributes:
            loopPtr = mesh.attributes['.corner_vert'].data[0].as_pointer()
        else:
            loopPtr = mesh.loops[0].as_pointer()

        if 'position' in mesh.attributes:
            vertPtr = mesh.attributes['position'].data[0].as_pointer()
        else:
            vertPtr = mesh.vertices[0].as_pointer()

        normalPtr = mesh.vertex_normals[0].as_pointer()
        loopUVsPtrList = []
        loopColsPtrList = []

        if mesh.uv_layers:
            for uv in mesh.uv_layers:
                if uv.name in mesh.attributes:
                    loopUVsPtrList.append(mesh.attributes[uv.name].data[0].as_pointer())
                else:
                    loopUVsPtrList.append(uv.data[0].as_pointer())
        else:
            loopUVsPtrList.append(0)

        if mesh.vertex_colors:
            for vcol in mesh.vertex_colors:
                if vcol.name in mesh.attributes:
                    loopColsPtrList.append(mesh.attributes[vcol.name].data[0].as_pointer())
                else:
                    loopColsPtrList.append(vcol.data[0].as_pointer())
        else:
            loopColsPtrList.append(0)

        meshPtr = mesh.as_pointer()

        material_indices = list([p.material_index for p in mesh.polygons])
        material_count = max(1, len(mesh.materials))

        if is_viewport_render or use_instancing:
            mesh_transform = None
        else:
            mesh_transform = utils.matrix_to_list(transform)

        sharp_attr = False
        sharpPtr = 0

        if 'sharp_face' in mesh.attributes:
            sharp_attr = True
            sharpPtr = mesh.attributes['sharp_face'].data[0].as_pointer()

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
                        mesh.calc_normals()
                    mesh.split_faces()

                mesh.calc_loop_triangles()

                if mesh.has_custom_normals:
                    mesh.calc_normals_split()

        yield mesh
    finally:
        if object_eval and mesh:
            object_eval.to_mesh_clear()
