from ..bin import pyluxcore
from .. import utils
from ..utils.errorlog import LuxCoreErrorLog

ERROR_VALUE = 0


def convert(material, props, luxcore_name, obj_name=""):
    output = material.node_tree.get_output_node("CYCLES")
    if output is None or not output.inputs["Surface"].is_linked:
        return black(luxcore_name)
    link = output.inputs["Surface"].links[0]
    result = convert_cycles_node(link.from_node, link.from_socket, props, luxcore_name, obj_name)
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
        link = socket.links[0]
        return convert_cycles_node(link.from_node, link.from_socket, props, obj_name=obj_name)
    else:
        if not hasattr(socket, "default_value"):
            return ERROR_VALUE

        try:
            return list(socket.default_value)[:3]
        except TypeError:
            # Not iterable
            return socket.default_value


def convert_cycles_node(node, output_socket, props, luxcore_name=None, obj_name=""):
    if luxcore_name is None:
        luxcore_name = str(node.as_pointer()) + utils.sanitize_luxcore_name(output_socket.name)

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
    elif node.bl_idname == "ShaderNodeMixShader":
        prefix = "scene.materials."

        def convert_mat_socket(index):
            mat_name = convert_cycles_socket(node.inputs[index], props, obj_name)
            if mat_name == ERROR_VALUE:
                mat_name, mat_props = black("__BLACK__")
                props.Set(mat_props)
            return mat_name

        definitions = {
            "type": "mix",
            "material1": convert_mat_socket(1),
            "material2": convert_mat_socket(2),
            "amount": convert_cycles_socket(node.inputs["Fac"], props, obj_name),
        }
    elif node.bl_idname == "ShaderNodeBsdfDiffuse":
        prefix = "scene.materials."
        # TODO roughmatte and roughness -> sigma conversion (if possible)
        definitions = {
            "type": "matte",
            "kd": convert_cycles_socket(node.inputs["Color"], props, obj_name),
        }
    elif node.bl_idname == "ShaderNodeBsdfGlossy":
        prefix = "scene.materials."

        # Implicitly create a fresnelcolor texture with unique name
        tex_name = luxcore_name + "fresnel_helper"
        helper_prefix = "scene.textures." + tex_name + "."
        helper_defs = {
            "type": "fresnelcolor",
            "kr": convert_cycles_socket(node.inputs["Color"], props, obj_name),
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))

        roughness = convert_cycles_socket(node.inputs["Roughness"], props, obj_name)

        definitions = {
            "type": "metal2",
            "fresnel": tex_name,
            "uroughness": roughness,
            "vroughness": roughness,
        }
    elif node.bl_idname == "ShaderNodeTexImage":
        if node.image:
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
                "file": utils.get_abspath(node.image.filepath),
                "wrap": extension_map[node.extension],
                "channel": "alpha" if output_socket == node.outputs["Alpha"] else "rgb",
                # Crude approximation, not sure if we can do better
                "gamma": 2.2 if node.image.colorspace_settings.name == "sRGB" else 1,
                "gain": 1,

                "mapping.type": "uvmapping2d",
                "mapping.uvscale": [1, -1],
                "mapping.rotation": 0,
                "mapping.uvdelta": [0, 1],
            }
        else:
            return [1, 0, 1]
    elif node.bl_idname == "ShaderNodeBsdfGlass":
        prefix = "scene.materials."
        color = convert_cycles_socket(node.inputs["Color"], props, obj_name)
        roughness = convert_cycles_socket(node.inputs["Roughness"], props, obj_name)

        definitions = {
            "type": "glass" if roughness == 0 else "roughglass",
            "kt": color,
            "kr": color, # Nonsense, maybe leave white even if it breaks compatibility with Cycles?
            "interiorior": convert_cycles_socket(node.inputs["IOR"], props, obj_name),
        }

        if roughness != 0:
            definitions["uroughness"] = roughness
            definitions["vroughness"] = roughness
    else:
        LuxCoreErrorLog.add_warning(f"Unknown node type: {node.name}", obj_name=obj_name)
        return ERROR_VALUE

    props.Set(utils.create_props(prefix + luxcore_name + ".", definitions))
    return luxcore_name
