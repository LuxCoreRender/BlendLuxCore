from contextlib import contextmanager
import bpy

# TODO 2.8

@contextmanager
def convert(obj, context, scene):
    """
    Create a temporary mesh from an object.
    The mesh is guaranteed to be removed when the calling block ends.
    Can return None if no mesh could be created from the object (e.g. for empties)

    Use it like this:

    with mesh_converter.convert(obj, context, scene) as mesh:
        if mesh:
            print(mesh.name)
            ...
    """

    mesh = None
    object_eval = None

    try:
        # apply_modifiers = True
        # modifier_mode = "PREVIEW" if context else "RENDER"
        # mesh = obj.to_mesh(scene, apply_modifiers, modifier_mode, calc_tessface=False)

        object_eval = obj.evaluated_get(depsgraph)
        if object_eval:
            mesh = object_eval.to_mesh()

            # if mesh:
            #     if mesh.use_auto_smooth and not mesh.has_custom_normals:
            #         mesh.calc_normals()
            #         mesh.split_faces()
            #     mesh.calc_tessface()

        yield mesh
    finally:
        if object_eval and mesh:
            # bpy.data.meshes.remove(mesh, do_unlink=False)

            # Remove temporary mesh.
            object_eval.to_mesh_clear()
