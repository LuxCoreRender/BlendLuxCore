import bpy
from ..bin import pyluxcore
from . import find_active_uv


def draw_uv_info(context, layout):
    """
    Call this function on nodes that use UV mapping (e.g. the Roughness class uses it
    when anisotropic roughness is enabled because it requires UV mapping).
    """
    if context.object.data:
        uv_textures = getattr(context.object.data, "uv_textures", [])
        if len(uv_textures) > 1:
            box = layout.box()
            box.label("LuxCore only supports one UV map", icon="INFO")
            active_uv = find_active_uv(context.object.data.uv_textures)
            box.label('Active: "%s"' % active_uv.name, icon="GROUP_UVS")
        elif len(uv_textures) == 0:
            layout.label("No UV map", icon="ERROR")


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
        layout.label("Transmitted: %.2f" % transmitted, icon="INFO")


def export_material_input(input, props):
    material_name = input.export(props)

    if material_name:
        return material_name
    else:
        print("WARNING: No material linked on input", input.name, "of node", input.node.name)
        luxcore_name = "__BLACK__"
        props.Set(pyluxcore.Property("scene.materials.%s.type" % luxcore_name, "matte"))
        props.Set(pyluxcore.Property("scene.materials.%s.kd" % luxcore_name, [0, 0, 0]))
        return luxcore_name


def get_linked_node(socket):
    if not socket.is_linked:
        return None
    return socket.links[0].from_node


def find_nodes(node_tree, bl_idname):
    return [node for node in node_tree.nodes if node.bl_idname == bl_idname]


def update_opengl_materials(_, context):
    if not hasattr(context, "object") or not context.object or not context.object.active_material:
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

            # Usually we want to show the color in the first input as main color
            socket = first_node.inputs[0]

            if socket.is_linked:
                # TODO (complicated topic)
                color_node = get_linked_node(socket)
                if color_node.bl_idname == "LuxCoreNodeTexImagemap":
                    ...
            elif hasattr(socket, "default_value"):
                diffuse_color = socket.default_value

    mat.diffuse_color = diffuse_color
