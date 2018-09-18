import bpy
from ..bin import pyluxcore
from .. import utils
from ..utils import ExportedObject
from ..utils import node as utils_node

from . import material, mesh_converter
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
    elif blender_obj.type == "EMPTY":
        return pyluxcore.Properties(), None

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

        is_shared_mesh = utils.can_share_mesh(blender_obj) and not dupli_suffix
        update_shared_mesh = False
        mesh_key = utils.make_key(blender_obj.data)
        mesh_definitions = None

        if is_shared_mesh:
            try:
                # Try to use the mesh_definitions created during the first export of this shared mesh
                mesh_definitions = exporter.shared_meshes[mesh_key]
                update_mesh = False
                # print("Object %s, Mesh %s: Got mesh_definitions from cache"
                #       % (blender_obj.name, blender_obj.data.name))
            except KeyError:
                # The shared mesh was not exported yet, this is the first time
                update_shared_mesh = True
                # print("Object %s, Mesh %s: Shared mesh not in cache yet"
                #       % (blender_obj.name, blender_obj.data.name))

        if update_mesh:
            # print("converting mesh:", blender_obj.data.name)
            with mesh_converter.convert(blender_obj, context, scene) as mesh:
                if mesh and mesh.tessfaces:
                    mesh_definitions = _convert_mesh_to_shapes(luxcore_name, mesh, luxcore_scene, mesh_transform)
                else:
                    # This is not worth a warning in the errorlog
                    print(blender_obj.name + ": No mesh data after to_mesh()")
                    return props, None

        if mesh_definitions is None:
            # This is the case if (not is_shared_mesh or update_shared_mesh)
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

            # The "Mesh-" prefix is hardcoded in Scene_DefineBlenderMesh1 in the LuxCore API
            lux_shape_name = "Mesh-" + lux_object_name
            if is_shared_mesh:
                # The object name saved in the mesh_definitons is incorrect, we have to replace it
                # (it's the one from the first time this mesh was exported)
                lux_object_name = luxcore_name + "%03d" % material_index

            _define_luxcore_object(props, lux_object_name, lux_shape_name, lux_mat_name, obj_transform,
                                   blender_obj, scene, context, duplicator)

        if update_shared_mesh:
            exporter.shared_meshes[mesh_key] = mesh_definitions

        return props, ExportedObject(mesh_definitions)
    except Exception as error:
        msg = 'Object "%s": %s' % (blender_obj.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()
        return pyluxcore.Properties(), None


def _handle_pointiness(props, lux_shape_name, blender_obj):
    use_pointiness = False

    for mat_slot in blender_obj.material_slots:
        mat = mat_slot.material
        if mat and mat.luxcore.node_tree:
            # Material with nodetree, check the nodes for pointiness node
            use_pointiness = utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexPointiness")

    if use_pointiness:
        pointiness_shape = lux_shape_name + "_pointiness"
        prefix = "scene.shapes." + pointiness_shape + "."
        props.Set(pyluxcore.Property(prefix + "type", "pointiness"))
        props.Set(pyluxcore.Property(prefix + "source", lux_shape_name))
        lux_shape_name = pointiness_shape

    return lux_shape_name


def _define_luxcore_object(props, lux_object_name, lux_shape_name, lux_material_name, obj_transform,
                           blender_obj, scene, context, duplicator):
    lux_shape_name = _handle_pointiness(props, lux_shape_name, blender_obj)
    prefix = "scene.objects." + lux_object_name + "."
    props.Set(pyluxcore.Property(prefix + "material", lux_material_name))

    props.Set(pyluxcore.Property(prefix + "shape", lux_shape_name))
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

    # TODO use the active_render setting like for UVs
    vertex_color = mesh.tessface_vertex_colors.active
    if vertex_color:
        vertexColors = vertex_color.data[0].as_pointer()
    else:
        vertexColors = 0

    return luxcore_scene.DefineBlenderMesh(name, len(mesh.tessfaces), faces, len(mesh.vertices),
                                           vertices, texCoords, vertexColors, mesh_transform)
