import bpy
from ..bin import pyluxcore
from .. import utils
from ..utils import ExportedObject

from . import material
from .light import convert_lamp

def convert(blender_obj, scene, context, luxcore_scene,
            exported_object=None, update_mesh=False, dupli_suffix="", matrix=None):

def convert(blender_obj, scene, context, luxcore_scene, exported_object=None, update_mesh=False, dupli_suffix="", matrix=None):
    if not utils.is_obj_visible(blender_obj, scene, context):
        return pyluxcore.Properties(), None

    if blender_obj.type == "LAMP":
        return convert_lamp(blender_obj, scene, context, luxcore_scene)

    try:
        print("converting object:", blender_obj.name)
        # Note that his is not the final luxcore_name, as the object may be split by DefineBlenderMesh()
        luxcore_name = utils.to_luxcore_name(blender_obj.name)+dupli_name_suffix
        props = pyluxcore.Properties()

        if blender_obj.data is None:
            # This is not worth a warning in the errorlog
            print(blender_obj.name + ": No mesh data")
            return props, None

        if update_mesh:
            print("converting mesh:", blender_obj.data.name)
            modifier_mode = "PREVIEW" if context else "RENDER"
            apply_modifiers = True
            mesh = blender_obj.to_mesh(scene, apply_modifiers, modifier_mode)

            if mesh is None or len(mesh.tessfaces) == 0:
                # This is not worth a warning in the errorlog
                print(blender_obj.name + ": No mesh data after to_mesh()")
                return props, None

            mesh_definitions = _convert_mesh_to_shapes(luxcore_name, mesh, luxcore_scene, matrix)
            bpy.data.meshes.remove(mesh, do_unlink=False)
        else:
            assert exported_object is not None
            print(blender_obj.name + ": Using cached mesh")
            mesh_definitions = exported_object.mesh_definitions

        transformation = utils.matrix_to_list(blender_obj.matrix_world, scene, apply_worldscale=True)

        for lux_object_name, material_index in mesh_definitions:
            if material_index < len(blender_obj.material_slots):
                mat = blender_obj.material_slots[material_index].material
                # TODO material cache
                lux_mat_name, mat_props = material.convert(mat, scene)

                if mat is None:
                    # Note: material.convert returned the fallback material in this case
                    msg = 'Object "%s": No material attached to slot %d' % (blender_obj.name, material_index)
                    scene.luxcore.errorlog.add_warning(msg)
            else:
                # The object has no material slots
                msg = 'Object "%s": No material defined' % blender_obj.name
                scene.luxcore.errorlog.add_warning(msg)
                # Use fallback material
                lux_mat_name, mat_props = material.fallback()

            props.Set(mat_props)
            _define_luxcore_object(props, lux_object_name, lux_mat_name, transformation)

        return props, ExportedObject(mesh_definitions)
    except Exception as error:
        msg = 'Object "%s": %s' % (blender_obj.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()
        return pyluxcore.Properties(), None


def _define_luxcore_object(props, lux_object_name, lux_material_name, transformation=None):
    # The "Mesh-" prefix is hardcoded in Scene_DefineBlenderMesh1 in the LuxCore API
    luxcore_shape_name = "Mesh-" + lux_object_name
    prefix = "scene.objects." + lux_object_name + "."
    props.Set(pyluxcore.Property(prefix + "material", lux_material_name))
    props.Set(pyluxcore.Property(prefix + "shape", luxcore_shape_name))
    if transformation:
        props.Set(pyluxcore.Property(prefix + "transformation", transformation))


def _convert_mesh_to_shapes(name, mesh, luxcore_scene, transformation=None):
    faces = mesh.tessfaces[0].as_pointer()
    vertices = mesh.vertices[0].as_pointer()

    uv_textures = mesh.tessface_uv_textures
    active_uv = utils.find_active_uv(uv_textures)
    if active_uv and active_uv.data:
        texCoords = active_uv.data[0].as_pointer()
    else:
        texCoords = 0

    vertex_color = mesh.tessface_vertex_colors.active
    if vertex_color:
        vertexColors = vertex_color.data[0].as_pointer()
    else:
        vertexColors = 0

    # TODO
    #transformation = None # if self.use_instancing else self.transformation            

    return luxcore_scene.DefineBlenderMesh(name, len(mesh.tessfaces), faces, len(mesh.vertices),
                                           vertices, texCoords, vertexColors, transformation)
