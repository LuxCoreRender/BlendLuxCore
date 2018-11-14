from contextlib import contextmanager
import bpy


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

    try:
        apply_modifiers = True
        modifier_mode = "PREVIEW" if context else "RENDER"
        mesh = obj.to_mesh(scene, apply_modifiers, modifier_mode, calc_tessface=False)

        if mesh:
            if mesh.use_auto_smooth and not mesh.has_custom_normals:
                mesh.calc_normals()
                mesh.split_faces()
            mesh.calc_tessface()

        yield mesh
    finally:
        if mesh:
            bpy.data.meshes.remove(mesh, do_unlink=False)
