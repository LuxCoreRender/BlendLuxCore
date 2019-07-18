from contextlib import contextmanager
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

        if mesh.uv_layers:
            # TODO get actual active layer
            active_uv_layer = 0
            loopUVsPtr = mesh.uv_layers[active_uv_layer].data[0].as_pointer()
        else:
            loopUVsPtr = 0

        if mesh.vertex_colors:
            # TODO get actual active layer
            active_vcol_layer = 0
            loopColsPtr = mesh.vertex_colors[active_vcol_layer].data[0].as_pointer()
        else:
            loopColsPtr = 0

        material_count = max(1, len(mesh.materials))

        if is_viewport_render or use_instancing:
            mesh_transform = None
        else:
            mesh_transform = utils.matrix_to_list(transform)

        mesh_definitions = luxcore_scene.DefineBlenderMesh(mesh_key, loopTriCount, loopTriPtr, loopPtr,
                                                           vertPtr, polyPtr, loopUVsPtr, loopColsPtr,
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

                # TODO autosmooth

            # if mesh:
            #     if mesh.use_auto_smooth and not mesh.has_custom_normals:
            #         mesh.calc_normals()
            #         mesh.split_faces()
            #     mesh.calc_tessface()

        yield mesh
    finally:
        if object_eval and mesh:
            object_eval.to_mesh_clear()
