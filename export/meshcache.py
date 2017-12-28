import bpy
import os
import tempfile
from .blender_object import ExportedObject
from .. import utils
from ..bin import pyluxcore


class MeshCache(object):
    temp_meshes = {}

    @classmethod
    def convert(cls, blender_obj, scene, context, luxcore_scene, props):
        # Note that his is not the final luxcore_name, as the object may be split by DefineBlenderMesh()
        luxcore_name = utils.to_luxcore_name(blender_obj.name)

        needs_export = False
        predicted_mesh_defs = _predict_mesh_definitions(blender_obj, luxcore_name)
        mesh_definitions = cls._load_meshes(predicted_mesh_defs, luxcore_scene, props)

        # TODO check if mesh was changed (scene udpate post handler)

        if len(mesh_definitions) == 0:
            # We could not load any meshes from disk
            print("converting mesh:", blender_obj.data.name)
            modifier_mode = "PREVIEW" if context else "RENDER"
            apply_modifiers = True
            mesh = blender_obj.to_mesh(scene, apply_modifiers, modifier_mode)

            if mesh is None or len(mesh.tessfaces) == 0:
                print("No mesh data after to_mesh()")
                return

            mesh_definitions = _convert_mesh_to_shapes(luxcore_name, mesh, luxcore_scene)
            bpy.data.meshes.remove(mesh, do_unlink=False)

        return mesh_definitions

    @classmethod
    def _load_meshes(cls, predicted_mesh_defs, luxcore_scene, props):
        # The predicted definitions might not be correct because we don't check each face
        # if the material is actually used, so we need to re-check if the object is in our cache
        mesh_definitions = []

        for lux_object_name, material_index in predicted_mesh_defs:
            name_shape = "Mesh-" + lux_object_name

            if lux_object_name in cls.temp_meshes:
                path = cls.temp_meshes[lux_object_name].name
                print("Reading", lux_object_name, "from disk. Path:", path)
                props.Set(pyluxcore.Property('scene.shapes.' + name_shape + '.type', 'mesh'))
                props.Set(pyluxcore.Property('scene.shapes.' + name_shape + '.ply', path))
                mesh_definitions.append([lux_object_name, material_index])
            else:
                print(lux_object_name, "is not in cls.temp_meshes")

        return mesh_definitions

    @classmethod
    def save_meshes(cls, luxcore_scene, exported_objects):
        print("Saving meshes")
        # TODO save only meshes with modifiers?
        # TODO test if DefineBlenderMesh or LoadMesh is faster

        for exported_object in exported_objects:
            if isinstance(exported_object, ExportedObject):
                for luxcore_name in exported_object.luxcore_names:
                    temp_file_path = cls._get_temp_file(luxcore_name)
                    luxcore_scene.SaveMesh(luxcore_name, temp_file_path)

    @classmethod
    def cleanup(cls):
        for temp_file in cls.temp_meshes.values():
            print("Deleting temporary mesh:", temp_file.name)
            os.remove(temp_file.name)

        cls.temp_meshes = {}

    @classmethod
    def _get_temp_file(cls, luxcore_name):
        if luxcore_name in cls.temp_meshes:
            # File for this mesh already exists
            temp_file = cls.temp_meshes[luxcore_name]
        else:
            # Create a new tempfile (bpy format is LuxCore's serialized mesh)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".bpy")
            cls.temp_meshes[luxcore_name] = temp_file

        return temp_file.name


def _predict_mesh_definitions(blender_obj, luxcore_name):
    mesh_definitions = []
    for mat_index in range(len(blender_obj.material_slots)):
        lux_obj_name = luxcore_name + "%03d" % mat_index
        mesh_definitions.append([lux_obj_name, mat_index])
    return mesh_definitions


def _convert_mesh_to_shapes(name, mesh, luxcore_scene):
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
    transformation = None  # if self.use_instancing else self.transformation

    return luxcore_scene.DefineBlenderMesh(name, len(mesh.tessfaces), faces, len(mesh.vertices),
                                           vertices, texCoords, vertexColors, transformation)
