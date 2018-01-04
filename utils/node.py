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
    nodes = []
    for node in node_tree.nodes:
        if node.bl_idname == bl_idname:
            nodes.append(node)

    return nodes
