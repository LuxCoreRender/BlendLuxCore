import bpy
from ..bin import pyluxcore
from .. import utils
from ..utils import ExportedObject
from ..utils import node as utils_node

from . import material
from .light import convert_lamp


def convert(exporter, blender_obj, scene, context, luxcore_scene,
            exported_object=None, update_mesh=False, dupli_suffix="", duplicator=None):
    """
    duplicator: The duplicator object that created this dupli (e.g. the particle emitter object)
    """

    if not utils.is_obj_visible(blender_obj, scene, context, is_dupli=dupli_suffix):
        return pyluxcore.Properties(), None

    if blender_obj.is_duplicator and not utils.is_duplicator_visible(blender_obj):
        return pyluxcore.Properties(), None

    if blender_obj.type == "LAMP":
        return convert_lamp(exporter, blender_obj, scene, context, luxcore_scene, dupli_suffix)

    try:
        # print("converting object:", blender_obj.name)
        # Note that his is not the final luxcore_name, as the object may be split by DefineBlenderMesh()
        luxcore_name = utils.get_luxcore_name(blender_obj, context) + dupli_suffix
        props = pyluxcore.Properties()

        if blender_obj.data is None:
            # This is not worth a warning in the errorlog
            print(blender_obj.name + ": No mesh data")
            return props, None

        transformation = utils.matrix_to_list(blender_obj.matrix_world, scene, apply_worldscale=True)

        # Instancing just means that we transform the object instead of the mesh
        if utils.use_instancing(blender_obj, scene, context) or dupli_suffix:
            obj_transform = transformation
            mesh_transform = None
        else:
            obj_transform = None
            mesh_transform = transformation

        if update_mesh:
            # print("converting mesh:", blender_obj.data.name)
            modifier_mode = "PREVIEW" if context else "RENDER"
            apply_modifiers = True
            mesh = blender_obj.to_mesh(scene, apply_modifiers, modifier_mode)

            if mesh is None or len(mesh.tessfaces) == 0:
                # This is not worth a warning in the errorlog
                print(blender_obj.name + ": No mesh data after to_mesh()")
                return props, None

            # mesh.calc_normals_split()
            # mesh.update(calc_edges=True, calc_tessface=True)
            mesh_definitions = _convert_mesh_to_shapes(luxcore_name, mesh, luxcore_scene, mesh_transform)
            bpy.data.meshes.remove(mesh, do_unlink=False)
        else:
            assert exported_object is not None
            print(blender_obj.name + ": Using cached mesh")
            mesh_definitions = exported_object.mesh_definitions

        render_layer = utils.get_current_render_layer(scene)
        override_mat = render_layer.material_override if render_layer else None

        for lux_object_name, material_index in mesh_definitions:
            if not context and override_mat:
                # Only use override material in final render
                lux_mat_name, mat_props = material.convert(exporter, override_mat, scene, context)
            else:
                if material_index < len(blender_obj.material_slots):
                    mat = blender_obj.material_slots[material_index].material
                    # TODO material cache
                    lux_mat_name, mat_props = material.convert(exporter, mat, scene, context)

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
            _define_luxcore_object(props, lux_object_name, lux_mat_name, obj_transform,
                                   blender_obj, scene, context, duplicator)

        return props, ExportedObject(mesh_definitions)
    except Exception as error:
        msg = 'Object "%s": %s' % (blender_obj.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()
        return pyluxcore.Properties(), None


def _handle_pointiness(props, luxcore_shape_name, blender_obj):
    use_pointiness = False

    for mat_slot in blender_obj.material_slots:
        mat = mat_slot.material
        if mat and mat.luxcore.node_tree:
            # Material with nodetree, check the nodes for pointiness node
            use_pointiness = utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexPointiness")

    if use_pointiness:
        pointiness_shape = luxcore_shape_name + "_pointiness"
        prefix = "scene.shapes." + pointiness_shape + "."
        props.Set(pyluxcore.Property(prefix + "type", "pointiness"))
        props.Set(pyluxcore.Property(prefix + "source", luxcore_shape_name))
        luxcore_shape_name = pointiness_shape

    return luxcore_shape_name


def _define_luxcore_object(props, lux_object_name, lux_material_name, obj_transform,
                           blender_obj, scene, context, duplicator):
    # The "Mesh-" prefix is hardcoded in Scene_DefineBlenderMesh1 in the LuxCore API
    luxcore_shape_name = "Mesh-" + lux_object_name
    luxcore_shape_name = _handle_pointiness(props, luxcore_shape_name, blender_obj)

    prefix = "scene.objects." + lux_object_name + "."
    props.Set(pyluxcore.Property(prefix + "material", lux_material_name))

    props.Set(pyluxcore.Property(prefix + "shape", luxcore_shape_name))
    if obj_transform:
        props.Set(pyluxcore.Property(prefix + "transformation", obj_transform))

    # In case of duplis, we have to check the camera visibility setting of the parent, not the dupli
    vis_obj = duplicator if duplicator else blender_obj
    visible_to_cam = utils.is_obj_visible_to_cam(vis_obj, scene, context)
    props.Set(pyluxcore.Property(prefix + "camerainvisible", not visible_to_cam))


def _convert_mesh_to_shapes(name, mesh, luxcore_scene, mesh_transform):
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

    return luxcore_scene.DefineBlenderMesh(name, len(mesh.tessfaces), faces, len(mesh.vertices),
                                           vertices, texCoords, vertexColors, mesh_transform)
