from ..bin import pyluxcore
from .. import utils
from ..utils import ExportedObject
from ..utils import node as utils_node

from . import material, mesh_converter
from .light import convert_lamp


EXPORTABLE_OBJECTS = {"MESH", "CURVE", "SURFACE", "META", "FONT", "LAMP", "EMPTY"}


def convert(exporter, obj, scene, context, luxcore_scene,
            exported_object=None, update_mesh=False,
            dupli_suffix="", dupli_matrix=None, duplicator=None):
    """
    duplicator: The duplicator object that created this dupli (e.g. the particle emitter object)
    """

    if not utils.is_obj_visible(obj, scene, context, is_dupli=dupli_suffix):
        return pyluxcore.Properties(), None

    if obj.is_duplicator and not utils.is_duplicator_visible(obj):
        return pyluxcore.Properties(), None

    if obj.type == "LAMP":
        return convert_lamp(exporter, obj, scene, context, luxcore_scene, dupli_suffix, dupli_matrix)
    elif obj.type == "EMPTY":
        return pyluxcore.Properties(), None

    try:
        # Note that his is not the final luxcore_name, as the object may be split by DefineBlenderMesh()
        luxcore_name = utils.get_luxcore_name(obj, context) + dupli_suffix
        props = pyluxcore.Properties()

        if obj.data is None:
            # This is not worth a warning in the errorlog
            print(obj.name + ": No mesh data")
            return props, None

        transformation = utils.matrix_to_list(obj.matrix_world, scene, apply_worldscale=True)

        # Instancing just means that we transform the object instead of the mesh
        if utils.use_instancing(obj, scene, context) or dupli_suffix:
            obj_transform = transformation
            mesh_transform = None
        else:
            obj_transform = None
            mesh_transform = transformation

        is_shared_mesh = utils.can_share_mesh(obj) and not dupli_suffix
        update_shared_mesh = False
        mesh_key = utils.make_key(obj.data)
        mesh_definitions = None

        if is_shared_mesh:
            try:
                # Try to use the mesh_definitions created during the first export of this shared mesh
                mesh_definitions = exporter.shared_meshes[mesh_key]
                update_mesh = False
            except KeyError:
                # The shared mesh was not exported yet, this is the first time
                update_shared_mesh = True

        if update_mesh:
            with mesh_converter.convert(obj, context, scene) as mesh:
                if mesh and mesh.tessfaces:
                    mesh_definitions = _convert_mesh_to_shapes(luxcore_name, mesh, luxcore_scene, mesh_transform)
                else:
                    # No mesh data. Happens e.g. on helper curves, so it is completely normal, don't warn about it.
                    return props, None

        if mesh_definitions is None:
            # This is the case if (not is_shared_mesh or update_shared_mesh)
            assert exported_object is not None
            print(obj.name + ": Using cached mesh")
            mesh_definitions = exported_object.mesh_definitions

        define_from_mesh_defs(mesh_definitions, scene, context, exporter, obj, props,
                              is_shared_mesh, luxcore_name, obj_transform, duplicator)

        if update_shared_mesh:
            exporter.shared_meshes[mesh_key] = mesh_definitions

        return props, ExportedObject(mesh_definitions, luxcore_name)
    except Exception as error:
        msg = 'Object "%s": %s' % (obj.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()
        return pyluxcore.Properties(), None


def define_from_mesh_defs(mesh_definitions, scene, context, exporter, obj, props,
                          is_shared_mesh, luxcore_name, obj_transform, duplicator):
    render_layer = utils.get_current_render_layer(scene)
    override_mat = render_layer.material_override if render_layer else None

    for lux_object_name, material_index in mesh_definitions:
        if not context and override_mat:
            # Only use override material in final render
            mat = override_mat
        else:
            if material_index < len(obj.material_slots):
                mat = obj.material_slots[material_index].material

                if mat is None:
                    # Note: material.convert returns the fallback material in this case
                    msg = 'Object "%s": No material attached to slot %d' % (obj.name, material_index)
                    scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)
            else:
                # The object has no material slots
                msg = 'Object "%s": No material defined' % obj.name
                scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)
                # Use fallback material
                mat = None

        if mat:
            if mat.luxcore.node_tree:
                imagemaps = utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexImagemap")
                if imagemaps and not utils_node.has_valid_uv_map(obj):
                    msg = ('Object "%s": %d image texture(s) used, but no UVs defined. ' 
                           'In case of bumpmaps this can lead to artifacts' % (obj.name, len(imagemaps)))
                    scene.luxcore.errorlog.add_warning(msg, obj_name=obj.name)

            lux_mat_name, mat_props = material.convert(exporter, mat, scene, context, obj.name)
        else:
            lux_mat_name, mat_props = material.fallback()

        props.Set(mat_props)

        # The "Mesh-" prefix is hardcoded in Scene_DefineBlenderMesh1 in the LuxCore API
        lux_shape_name = "Mesh-" + lux_object_name
        if is_shared_mesh:
            # The object name saved in the mesh_definitons is incorrect, we have to replace it
            # (it's the one from the first time this mesh was exported)
            lux_object_name = luxcore_name + "%03d" % material_index

        _define_luxcore_object(props, lux_object_name, lux_shape_name, lux_mat_name, obj_transform,
                               obj, mat, scene, context, duplicator)


def _handle_pointiness(props, lux_shape_name, mat):
    use_pointiness = False

    if mat and mat.luxcore.node_tree:
        # Material with nodetree, check the nodes for pointiness node
        # Note: it would be more correct to check if the pointiness node is actually connected and used
        use_pointiness = utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexPointiness")

    if use_pointiness:
        pointiness_shape = lux_shape_name + "_pointiness"
        prefix = "scene.shapes." + pointiness_shape + "."
        props.Set(pyluxcore.Property(prefix + "type", "pointiness"))
        props.Set(pyluxcore.Property(prefix + "source", lux_shape_name))
        lux_shape_name = pointiness_shape

    return lux_shape_name


def _define_luxcore_object(props, lux_object_name, lux_shape_name, lux_material_name, obj_transform,
                           obj, mat, scene, context, duplicator):
    lux_shape_name = _handle_pointiness(props, lux_shape_name, mat)
    prefix = "scene.objects." + lux_object_name + "."

    props.Set(pyluxcore.Property(prefix + "material", lux_material_name))
    props.Set(pyluxcore.Property(prefix + "shape", lux_shape_name))

    if obj.luxcore.id == -1:
        # We calculate the "random" object ID from the object name and, in case of dupli groups,
        # add the duplicator name so different group instances get different IDs
        object_id_source = obj.name
        if duplicator:
            object_id_source += duplicator.name
        obj_id = utils.make_object_id(object_id_source)
    else:
        obj_id = obj.luxcore.id
    props.Set(pyluxcore.Property(prefix + "id", obj_id))

    if obj_transform:
        props.Set(pyluxcore.Property(prefix + "transformation", obj_transform))

    # In case of duplis, we have to check the camera visibility setting of the parent, not the dupli
    vis_obj = duplicator if duplicator else obj
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

    vertex_colors = mesh.tessface_vertex_colors
    active_vertcol = utils.find_active_vertex_color_layer(vertex_colors)
    if active_vertcol and active_vertcol.data:
        vertexColors = active_vertcol.data[0].as_pointer()
    else:
        vertexColors = 0

    return luxcore_scene.DefineBlenderMesh(name, len(mesh.tessfaces), faces, len(mesh.vertices),
                                           vertices, texCoords, vertexColors, mesh_transform)
