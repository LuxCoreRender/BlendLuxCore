from ..bin import pyluxcore
from .. import utils
from ..utils.errorlog import LuxCoreErrorLog


def convert(material, props, luxcore_name, obj_name=""):
    output = material.node_tree.get_output_node("CYCLES")
    if output is None or not output.inputs["Surface"].is_linked:
        return black(luxcore_name)
    node = output.inputs["Surface"].links[0].from_node
    result = convert_cycles_node(node, props, luxcore_name, obj_name)
    if result == 0:
        return black(luxcore_name)
    return luxcore_name, props


def black(luxcore_name):
    props = pyluxcore.Properties()
    props.SetFromString("""
    scene.materials.{mat_name}.type = matte
    scene.materials.{mat_name}.kd = 0
    """.format(mat_name=luxcore_name))
    return luxcore_name, props


def convert_cycles_socket(socket, props, obj_name=""):
    # TODO use more advanced functions from our own socket base class (bypass reroutes etc.)
    if socket.is_linked:
        return convert_cycles_node(socket.links[0].from_node, props, obj_name=obj_name)
    else:
        try:
            return list(socket.default_value)[:3]
        except TypeError:
            # Not iterable
            return socket.default_value


def convert_cycles_node(node, props, luxcore_name=None, obj_name=""):
    if node.bl_idname == "ShaderNodeBsdfPrincipled":
        prefix = "scene.materials."
        definitions = {
            "type": "disney",
            "basecolor": convert_cycles_socket(node.inputs["Base Color"], props, obj_name),
            "subsurface": 0,
            "metallic": convert_cycles_socket(node.inputs["Metallic"], props, obj_name),
            "specular": convert_cycles_socket(node.inputs["Specular"], props, obj_name),
            "speculartint": convert_cycles_socket(node.inputs["Specular Tint"], props, obj_name),
            "roughness": convert_cycles_socket(node.inputs["Roughness"], props, obj_name),
            "anisotropic": convert_cycles_socket(node.inputs["Anisotropic"], props, obj_name),
            "sheen": convert_cycles_socket(node.inputs["Sheen"], props, obj_name),
            "sheentint": convert_cycles_socket(node.inputs["Sheen Tint"], props, obj_name),
            "clearcoat": convert_cycles_socket(node.inputs["Clearcoat"], props, obj_name),
            #"clearcoatgloss": convert_cycles_socket(node.inputs["Clearcoat Roughness"], props, obj_name), # TODO
        }
    elif node.bl_idname == "ShaderNodeTexImage":
        prefix = "scene.textures."
        extension_map = {
            "REPEAT": "repeat",
            "EXTEND": "clamp",
            "CLIP": "black",
        }
        definitions = {
            "type": "imagemap",
            # TODO get filepath with image exporter (because of packed files)
            # TODO image sequences
            "file": node.image.filepath,
            "wrap": extension_map[node.extension],
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": [1, -1],
            "mapping.rotation": 0,
            "mapping.uvdelta": [0, 1],
        }
    else:
        LuxCoreErrorLog.add_warning(f"Unknown node type: {node.name}", obj_name=obj_name)
        return 0

    if luxcore_name is None:
        luxcore_name = str(node.as_pointer())
    props.Set(utils.create_props(prefix + luxcore_name + ".", definitions))
    return luxcore_name
