import bpy
from ..bin import pyluxcore
from .. import utils
from ..utils import ExportedObject

from . import material
from .light import convert as convert_light


def convert(blender_obj, scene, context, luxcore_scene):
    if blender_obj.type == "LAMP":
        return convert_light(blender_obj, scene)

    try:
        print("converting object:", blender_obj.name)
        # Note that his is not the final luxcore_name, as the object may be split by DefineBlenderMesh()
        luxcore_name = utils.to_luxcore_name(blender_obj.name)
        props = pyluxcore.Properties()

        if blender_obj.data is None:
            print("No mesh data")
            return props

        modifier_mode = "PREVIEW" if context else "RENDER"
        apply_modifiers = True
        mesh = blender_obj.to_mesh(scene, apply_modifiers, modifier_mode)

        if mesh is None or len(mesh.tessfaces) == 0:
            print("No mesh data after to_mesh()")
            return props

        mesh_definitions = _convert_mesh_to_shapes(luxcore_name, mesh, luxcore_scene)
        bpy.data.meshes.remove(mesh, do_unlink=False)

        for lux_object_name, material_index in mesh_definitions:
            if material_index < len(blender_obj.material_slots):
                mat = blender_obj.material_slots[material_index].material
                # TODO material cache
                lux_mat_name, mat_props = material.convert(mat)
            else:
                # The object has no material slots
                lux_mat_name, mat_props = material.fallback()

            props.Set(mat_props)

            transformation = utils.matrix_to_list(blender_obj.matrix_world, scene)
            _define_luxcore_object(props, lux_object_name, lux_mat_name, transformation)

        luxcore_names = [lux_obj_name for lux_obj_name, material_index in mesh_definitions]
        return props, ExportedObject(luxcore_names)
    except Exception as error:
        # TODO: collect exporter errors
        print("ERROR in object", blender_obj.name)
        print(error)
        return pyluxcore.Properties()


def _define_luxcore_object(props, lux_object_name, lux_material_name, transformation=None):
    # This prefix is hardcoded in Scene_DefineBlenderMesh1 in the LuxCore API
    luxcore_shape_name = "Mesh-" + lux_object_name
    prefix = "scene.objects." + lux_object_name + "."
    props.Set(pyluxcore.Property(prefix + "material", lux_material_name))
    props.Set(pyluxcore.Property(prefix + "shape", luxcore_shape_name))
    if transformation:
        props.Set(pyluxcore.Property(prefix + "transformation", transformation))


def _convert_mesh_to_shapes(name, mesh, luxcore_scene):
    faces = mesh.tessfaces[0].as_pointer()
    vertices = mesh.vertices[0].as_pointer()

    uv_textures = mesh.tessface_uv_textures
    if len(uv_textures) > 0 and mesh.uv_textures.active and uv_textures.active.data:
        texCoords = uv_textures.active.data[0].as_pointer()
    else:
        texCoords = 0

    vertex_color = mesh.tessface_vertex_colors.active
    if vertex_color:
        vertexColors = vertex_color.data[0].as_pointer()
    else:
        vertexColors = 0

    # TODO
    transformation = None # if self.use_instancing else self.transformation

    return luxcore_scene.DefineBlenderMesh(name, len(mesh.tessfaces), faces, len(mesh.vertices),
                                           vertices, texCoords, vertexColors, transformation)