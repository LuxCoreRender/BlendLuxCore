from contextlib import contextmanager
import numpy as np
from .. import utils
from .caches.exported_data import ExportedMesh


def convert(obj, mesh_key, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform):
    with _prepare_mesh(obj, depsgraph) as mesh:
        if mesh is None:
            return None

        loopTriPtr = mesh.loop_triangles[0].as_pointer()
        loopTriCount = len(mesh.loop_triangles)
        loopPtr = mesh.loops[0].as_pointer()
        vertPtr = mesh.vertices[0].as_pointer()
        polyPtr = mesh.polygons[0].as_pointer()

        loopUVsPtrList = []
        loopColsPtrList = []

        if mesh.uv_layers:
            for uv in mesh.uv_layers:
                loopUVsPtrList.append(uv.data[0].as_pointer())
        else:
            loopUVsPtrList.append(0)

        if mesh.vertex_colors:
            for vcol in mesh.vertex_colors:
                loopColsPtrList.append(vcol.data[0].as_pointer())
        else:
            loopColsPtrList.append(0)

        material_count = max(1, len(mesh.materials))

        if is_viewport_render or use_instancing:
            mesh_transform = None
        else:
            mesh_transform = utils.matrix_to_list(transform)

        nploopUVsPtrList = np.array(loopUVsPtrList, dtype=np.uintp)
        nploopColsPtrList = np.array(loopColsPtrList, dtype=np.uintp)

        if len(loopUVsPtrList) <= 1 and len(loopColsPtrList) <= 1:
            loopUVsPtr = 0
            loopColsPtr = 0
            if mesh.uv_layers:
                loopUVsPtr = mesh.uv_layers[0].data[0].as_pointer()
            if mesh.vertex_colors:
                loopColsPtr = mesh.vertex_colors[0].data[0].as_pointer()

            mesh_definitions = luxcore_scene.DefineBlenderMesh(mesh_key, loopTriCount, loopTriPtr, loopPtr,
                                                               vertPtr, polyPtr, loopUVsPtr, loopColsPtr,
                                                               material_count, mesh_transform)
        else:
            mesh_definitions = luxcore_scene.DefineBlenderMeshExt(mesh_key, loopTriCount, loopTriPtr, loopPtr,
                                                                  vertPtr, polyPtr, nploopUVsPtrList, nploopColsPtrList,
                                                                  material_count, mesh_transform)

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
                mesh.calc_loop_triangles()
                if not mesh.loop_triangles:
                    object_eval.to_mesh_clear()
                    mesh = None

            if mesh:
                if mesh.use_auto_smooth and not mesh.has_custom_normals:
                    mesh.calc_normals()
                    mesh.split_faces()
                mesh.calc_loop_triangles()

        yield mesh
    finally:
        if object_eval and mesh:
            object_eval.to_mesh_clear()
