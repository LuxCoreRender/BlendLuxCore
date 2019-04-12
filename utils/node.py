import mathutils
from ..bin import pyluxcore
from . import find_active_uv
from ..ui import icons


def draw_uv_info(context, layout):
    """
    Call this function on nodes that use UV mapping (e.g. the Roughness class uses it
    when anisotropic roughness is enabled because it requires UV mapping).
    """
    obj = context.object

    def warning_no_uvmap(_layout):
        _layout.label("No UV map", icon=icons.WARNING)

    if obj and obj.data:
        if obj.type in {"CURVE", "SURFACE", "FONT"}:
            if not obj.data.use_uv_as_generated:
                row = layout.row()
                warning_no_uvmap(row)
                row.prop(obj.data, "use_uv_as_generated", toggle=True, text="Enable UV")
        elif obj.type == "MESH":
            if len(obj.data.uv_textures) > 1:
                box = layout.box()
                box.label("LuxCore only supports one UV map", icon=icons.INFO)
                active_uv = find_active_uv(obj.data.uv_textures)
                box.label('Active: "%s"' % active_uv.name, icon="GROUP_UVS")
            elif len(obj.data.uv_textures) == 0:
                row = layout.row()
                warning_no_uvmap(row)
                row.operator("mesh.uv_texture_add")
        else:
            warning_no_uvmap(layout)


def has_valid_uv_map(obj):
    if not obj.data:
        return False

    if obj.type in {"CURVE", "SURFACE", "FONT"}:
        if not obj.data.use_uv_as_generated:
            return False
    elif obj.type == "MESH" and len(obj.data.uv_textures) == 0:
        return False

    return True


def draw_transmission_info(node, layout):
    try:
        kd_socket = node.inputs["Diffuse Color"]
    except KeyError:
        # For some reason, this socket is named differently in the mattetranslucent material
        kd_socket = node.inputs["Reflection Color"]

    kt_socket = node.inputs["Transmission Color"]

    if not kd_socket.is_linked and not kt_socket.is_linked:
        # V component of the HSV color model
        kd_value = kd_socket.default_value.v
        kt_value = kt_socket.default_value.v
        # Note that this is an estimation.
        # We are for example not accounting for specular reflections
        transmitted = min(1 - kd_value, kt_value)
        layout.label("Transmitted: %.2f" % transmitted, icon=icons.INFO)


def export_material_input(input, exporter, props, luxcore_name=None):
    material_name = input.export(exporter, props, luxcore_name)

    if material_name:
        return material_name
    else:
        print("WARNING: No material linked on input", input.name, "of node", input.node.name)
        if luxcore_name is None:
            luxcore_name = "__BLACK__"
        props.Set(pyluxcore.Property("scene.materials.%s.type" % luxcore_name, "matte"))
        props.Set(pyluxcore.Property("scene.materials.%s.kd" % luxcore_name, [0, 0, 0]))
        return luxcore_name


def get_linked_node(socket):
    if not socket.is_linked:
        return None
    return socket.links[0].from_node


def find_nodes(node_tree, bl_idname):
    result = []

    for node in node_tree.nodes:
        if node.bl_idname == "LuxCoreNodeTreePointer" and node.node_tree:
            result += find_nodes(node.node_tree, bl_idname)
        if node.bl_idname == bl_idname:
            result.append(node)

    return result


def update_opengl_materials(_, context):
    if not hasattr(context, "object") or not context.object or not context.object.active_material or not context.object.active_material.luxcore.auto_vp_color:
        return

    mat = context.object.active_material
    node_tree = mat.luxcore.node_tree
    diffuse_color = (0, 0, 0)

    if node_tree is None:
        mat.diffuse_color = (0.5, 0.5, 0.5)
        return

    from ..nodes.output import get_active_output
    output = get_active_output(node_tree)

    if output:
        first_node = get_linked_node(output.inputs["Material"])

        if first_node:
            # Set default color for nodes without color sockets, e.g. mix or glossy coating
            diffuse_color = (0.5, 0.5, 0.5)

            if first_node.inputs:
                # Usually we want to show the color in the first input as main color
                socket = first_node.inputs[0]
                socket_value = getattr(socket, "default_value", None)

                if not socket.is_linked and isinstance(socket_value, mathutils.Color):
                    diffuse_color = socket_value

    mat.diffuse_color = diffuse_color


def copy_links_after_socket_swap(socket1, socket2, was_socket1_enabled):
    """
    Copy socket links from the output socket that was disabled to the one that was enabled.
    This function should be used on nodes that have two different output sockets which are
    enabled or disabled in turn depending on settings of the node.
    Example: the smoke node (color output when color grid is selected, value output otherwise).
    """
    node_tree = socket1.id_data
    if was_socket1_enabled == socket1.enabled:
        # Nothing changed
        pass
    elif was_socket1_enabled and not socket1.enabled:
        # socket1 was disabled while socket2 was enabled
        for link in socket1.links:
            node_tree.links.new(socket2, link.to_socket)
    else:
        # socket2 was disabled while socket1 was enabled
        for link in socket2.links:
            node_tree.links.new(socket1, link.to_socket)


def get_links(node_tree, socket):
    """List of node links from or to this socket"""
    return tuple(link for link in node_tree.links
                 if (link.from_socket == socket or
                     link.to_socket == socket))


def is_allowed_input(socket, input_socket):
    if not hasattr(socket, "allowed_inputs"):
        return True
    for allowed_class in socket.allowed_inputs:
        if isinstance(input_socket, allowed_class):
            return True
    return False
