from ..bin import pyluxcore
from .. import utils
from ..utils import node as utils_node
from ..utils.errorlog import LuxCoreErrorLog
from .image import ImageExporter
from mathutils import Matrix

ERROR_VALUE = 0
MISSING_IMAGE_COLOR = [1, 0, 1]

math_operation_map = {
    "MULTIPLY": "scale",
    "GREATER_THAN": "greaterthan",
    "LESS_THAN": "lessthan",
}


def convert(material, props, luxcore_name, obj_name=""):
    # print("Converting Cycles node tree of material", material.name_full)
    output = material.node_tree.get_output_node("CYCLES")
    if output is None:
        return black(luxcore_name)

    link = utils_node.get_link(output.inputs["Surface"])
    if link is None:
        return black(luxcore_name)

    result = _node(link.from_node, link.from_socket, props, luxcore_name, obj_name)
    if result == ERROR_VALUE:
        return black(luxcore_name)

    assert result == luxcore_name
    return luxcore_name, props


def black(luxcore_name="__BLACK__"):
    props = pyluxcore.Properties()
    props.SetFromString("""
    scene.materials.{mat_name}.type = matte
    scene.materials.{mat_name}.kd = 0
    """.format(mat_name=luxcore_name))
    return luxcore_name, props


def _socket(socket, props, obj_name, group_node):
    link = utils_node.get_link(socket)
    if link:
        return _node(link.from_node, link.from_socket, props, None, obj_name, group_node)

    if not hasattr(socket, "default_value"):
        return ERROR_VALUE

    try:
        return list(socket.default_value)[:3]
    except TypeError:
        # Not iterable
        return socket.default_value


def _node(node, output_socket, props, luxcore_name=None, obj_name="", group_node=None):
    if luxcore_name is None:
        luxcore_name = str(node.as_pointer()) + output_socket.name
        if group_node:
            luxcore_name += str(group_node.as_pointer())
        luxcore_name = utils.sanitize_luxcore_name(luxcore_name)

    if node.bl_idname == "ShaderNodeBsdfPrincipled":
        prefix = "scene.materials."
        definitions = {
            "type": "disney",
            "basecolor": _socket(node.inputs["Base Color"], props, obj_name, group_node),
            "subsurface": 0,  # TODO
            "metallic": _socket(node.inputs["Metallic"], props, obj_name, group_node),
            "specular": _socket(node.inputs["Specular"], props, obj_name, group_node),
            "speculartint": _socket(node.inputs["Specular Tint"], props, obj_name, group_node),
            # Both LuxCore and Cycles use squared roughness here, no need to convert
            "roughness": _socket(node.inputs["Roughness"], props, obj_name, group_node),
            "anisotropic": _socket(node.inputs["Anisotropic"], props, obj_name, group_node),
            "sheen": _socket(node.inputs["Sheen"], props, obj_name, group_node),
            "sheentint": _socket(node.inputs["Sheen Tint"], props, obj_name, group_node),
            "clearcoat": _socket(node.inputs["Clearcoat"], props, obj_name, group_node),
            #"clearcoatgloss": convert_cycles_socket(node.inputs["Clearcoat Roughness"], props, obj_name, group_node),  # TODO
            # TODO: emission, alpha, transmission, transmission roughness
        }
    elif node.bl_idname == "ShaderNodeMixShader":
        prefix = "scene.materials."

        def convert_mat_socket(index):
            mat_name = _socket(node.inputs[index], props, obj_name, group_node)
            if mat_name == ERROR_VALUE:
                mat_name, mat_props = black()
                props.Set(mat_props)
            return mat_name

        fac_input = node.inputs["Fac"]
        amount = _socket(fac_input, props, obj_name, group_node)
        if fac_input.is_linked and amount == ERROR_VALUE:
            amount = 0.5

        definitions = {
            "type": "mix",
            "material1": convert_mat_socket(1),
            "material2": convert_mat_socket(2),
            "amount": amount,
        }
    elif node.bl_idname == "ShaderNodeBsdfDiffuse":
        prefix = "scene.materials."
        # TODO roughmatte and roughness -> sigma conversion (if possible)
        definitions = {
            "type": "matte",
            "kd": _socket(node.inputs["Color"], props, obj_name, group_node),
        }
    elif node.bl_idname == "ShaderNodeBsdfGlossy":
        prefix = "scene.materials."

        # Implicitly create a fresnelcolor texture with unique name
        tex_name = luxcore_name + "fresnel_helper"
        helper_prefix = "scene.textures." + tex_name + "."
        helper_defs = {
            "type": "fresnelcolor",
            "kr": _socket(node.inputs["Color"], props, obj_name, group_node),
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))

        roughness = _squared_roughness_to_linear(node.inputs["Roughness"], props,
                                                 luxcore_name, obj_name, group_node)

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

            try:
                filepath = ImageExporter.export_cycles_node_reader(node.image)
            except OSError as error:
                LuxCoreErrorLog.add_warning(f"Image error: {error}", obj_name=obj_name)
                return MISSING_IMAGE_COLOR

            definitions = {
                "type": "imagemap",
                # TODO image sequences
                "file": filepath,
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
            return MISSING_IMAGE_COLOR
    elif node.bl_idname == "ShaderNodeBsdfGlass":
        prefix = "scene.materials."
        color = _socket(node.inputs["Color"], props, obj_name, group_node)
        roughness = _squared_roughness_to_linear(node.inputs["Roughness"], props,
                                                 luxcore_name, obj_name, group_node)

        definitions = {
            "type": "glass" if roughness == 0 else "roughglass",
            "kt": color,
            "kr": color, # Nonsense, maybe leave white even if it breaks compatibility with Cycles?
            "interiorior": _socket(node.inputs["IOR"], props, obj_name, group_node),
        }

        if roughness != 0:
            definitions["uroughness"] = roughness
            definitions["vroughness"] = roughness
    elif node.bl_idname == "ShaderNodeBsdfAnisotropic":
        prefix = "scene.materials."

        # Implicitly create a fresnelcolor texture with unique name
        tex_name = luxcore_name + "fresnel_helper"
        helper_prefix = "scene.textures." + tex_name + "."
        helper_defs = {
            "type": "fresnelcolor",
            "kr": _socket(node.inputs["Color"], props, obj_name, group_node),
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))

        # TODO emulate actual anisotropy and rotation somehow ...
        roughness = _squared_roughness_to_linear(node.inputs["Roughness"], props,
                                                 luxcore_name, obj_name, group_node)

        definitions = {
            "type": "metal2",
            "fresnel": tex_name,
            "uroughness": roughness,
            "vroughness": 0.05,
        }
    elif node.bl_idname == "ShaderNodeBsdfTranslucent":
        prefix = "scene.materials."
        definitions = {
            "type": "mattetranslucent",
            # TODO kt and kr don't really match Cycles result yet
            "kt": [1, 1, 1],
            "kr": _socket(node.inputs["Color"], props, obj_name, group_node),
        }
    elif node.bl_idname == "ShaderNodeBsdfTransparent":
        prefix = "scene.materials."
        definitions = {
            "type": "null",
        }
        color = _socket(node.inputs["Color"], props, obj_name, group_node)
        if color != 1 and color != [1, 1, 1]:
            definitions["transparency"] = color
    elif node.bl_idname == "ShaderNodeMixRGB":
        # TODO (in LuxCore):
        #  "DARKEN", "BURN", "LIGHTEN", "SCREEN", "DODGE", "OVERLAY", "SOFT_LIGHT",
        #  "LINEAR_LIGHT", "DIFFERENCE", "HUE", "SATURATION", "COLOR", "VALUE"

        prefix = "scene.textures."
        definitions = {}

        fac_input = node.inputs["Fac"]
        fac = _socket(fac_input, props, obj_name, group_node)
        if fac_input.is_linked and fac == ERROR_VALUE:
            fac = 0.5

        tex1 = _socket(node.inputs["Color1"], props, obj_name, group_node)
        tex2 = _socket(node.inputs["Color2"], props, obj_name, group_node)

        if fac == 0:
            return tex1

        blend_type = node.blend_type
        if blend_type in {"MIX", "MULTIPLY", "ADD", "SUBTRACT", "DIVIDE"}:
            if blend_type == "MULTIPLY":
                definitions["type"] = "scale"
            else:
                definitions["type"] = blend_type.lower()

            definitions["texture1"] = tex1
            definitions["texture2"] = tex2

            if blend_type == "MIX":
                definitions["amount"] = fac
                if fac == 1:
                    print("yolo")
                    return tex2
        else:
            LuxCoreErrorLog.add_warning(f"Unknown MixRGB mode: {blend_type}", obj_name=obj_name)
            return ERROR_VALUE

        if (isinstance(fac, str) or (fac > 0 and fac < 1)) and blend_type != "MIX":
            # Here we need to insert a helper texture *after* the current texture
            props.Set(utils.create_props(prefix + luxcore_name + ".", definitions))
            definitions = {
                "type": "mix",
                "texture1": tex1,
                "texture2": luxcore_name,
                "amount": fac,
            }
            luxcore_name = luxcore_name + "fac"
    elif node.bl_idname == "ShaderNodeMath":
        # TODO (in LuxCore):
        #  "LOGARITHM", "SQRT", "MINIMUM", "MAXIMUM",
        #  "FLOOR", "CEIL", "FRACT", "SINE", "COSINE", "TANGENT",
        #  "ARCSINE", "ARCCOSINE", "ARCTANGENT", "ARCTAN2"]

        prefix = "scene.textures."
        definitions = {}

        tex1 = _socket(node.inputs[0], props, obj_name, group_node)
        tex2 = _socket(node.inputs[1], props, obj_name, group_node)

        # In Cycles, the inputs are converted to float values (e.g. averaged in case of RGB input).
        # The following LuxCore textures would perform RGB operations if we didn't convert the inputs to floats.
        if node.operation in {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "ABSOLUTE"}:
            def convert_to_float(input_tex_name):
                # This is more or less a hack because we don't have a dedicated "RGB to BW" texture
                tex_name = input_tex_name + "to_float"
                helper_prefix = "scene.textures." + tex_name + "."
                helper_defs = {
                    "type": "power",
                    "base": input_tex_name,
                    "exponent": 1,
                }
                props.Set(utils.create_props(helper_prefix, helper_defs))
                return tex_name

            if isinstance(tex1, str):
                tex1 = convert_to_float(tex1)
            elif isinstance(tex1, list):
                tex1 = sum(tex1) / len(tex1)

            if isinstance(tex2, str):
                tex2 = convert_to_float(tex2)
            elif isinstance(tex2, list):
                tex2 = sum(tex2) / len(tex2)

        if node.operation in {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "GREATER_THAN", "LESS_THAN"}:
            try:
                definitions["type"] = math_operation_map[node.operation]
            except KeyError:
                definitions["type"] = node.operation.lower()
            definitions["texture1"] = tex1
            definitions["texture2"] = tex2
        elif node.operation == "POWER":
            definitions["type"] = "power"
            definitions["base"] = tex1
            definitions["exponent"] = tex2
        elif node.operation == "ABSOLUTE":
            definitions["type"] = "abs"
            definitions["texture"] = tex1
        elif node.operation == "ROUND":
            definitions["type"] = "rounding"
            definitions["texture"] = tex1
            definitions["increment"] = 1
        elif node.operation == "MODULO":
            definitions["type"] = "modulo"
            definitions["texture"] = tex1
            definitions["modulo"] = tex2
        else:
            LuxCoreErrorLog.add_warning(f"Unknown Math mode: {node.operation}", obj_name=obj_name)
            return ERROR_VALUE
    elif node.bl_idname == "ShaderNodeHueSaturation":
        prefix = "scene.textures."

        hue = _socket(node.inputs["Hue"], props, obj_name, group_node)
        saturation = _socket(node.inputs["Saturation"], props, obj_name, group_node)
        value = _socket(node.inputs["Value"], props, obj_name, group_node)
        fac = _socket(node.inputs["Fac"], props, obj_name, group_node)  # TODO
        color = _socket(node.inputs["Color"], props, obj_name, group_node)

        definitions = {
            "type": "hsv",
            "texture": color,
            "hue": hue,
            "saturation": saturation,
            "value": value,
        }
    elif node.bl_idname == "ShaderNodeGroup":
        active_output = None
        for subnode in node.node_tree.nodes:
            if subnode.bl_idname == "NodeGroupOutput" and subnode.is_active_output:
                active_output = subnode
                break

        current_input = active_output.inputs[output_socket.name]
        if not current_input.is_linked:
            return ERROR_VALUE

        link = utils_node.get_link(current_input)
        # I call _node instead of _socket here because I need to pass the
        # luxcore_name in case the node group is the first node in the tree
        return _node(link.from_node, link.from_socket, props, luxcore_name, obj_name, node)
    elif node.bl_idname == "NodeGroupInput":
        # TODO I set group_node to None, but what about nested groups?
        if group_node is None:
            LuxCoreErrorLog.add_warning("Nested groups are not supported yet", obj_name=obj_name)
            return ERROR_VALUE
        return _socket(group_node.inputs[output_socket.name], props, obj_name, None)
    elif node.bl_idname == "ShaderNodeEmission":
        prefix = "scene.materials."

        # According to the Blender manual, strength is in Watts/m² when the node is used on meshes.
        strength = _socket(node.inputs["Strength"], props, obj_name, group_node)

        definitions = {
            "type": "matte",
            "kd": [0, 0, 0],
            "emission": _socket(node.inputs["Color"], props, obj_name, group_node),
            "emission.gain": [strength] * 3,
            "emission.power": 0,
            "emission.efficency": 0,
        }
    elif node.bl_idname == "ShaderNodeValue":
        prefix = "scene.textures."

        definitions = {
            "type": "constfloat1",
            "value": node.outputs[0].default_value,
        }
    elif node.bl_idname == "ShaderNodeRGB":
        prefix = "scene.textures."

        definitions = {
            "type": "constfloat3",
            "value": list(node.outputs[0].default_value)[:3],
        }
    elif node.bl_idname == "ShaderNodeValToRGB":
        # Color ramp
        prefix = "scene.textures."
        ramp = node.color_ramp

        if ramp.interpolation == "CONSTANT":
            interpolation = "none"
        elif ramp.interpolation == "LINEAR":
            interpolation = "linear"
        else:
            # TODO: not all interpolation modes are supported by LuxCore
            interpolation = "cubic"

        definitions = {
            "type": "band",
            "amount": _socket(node.inputs["Fac"], props, obj_name, group_node),
            "offsets": len(ramp.elements),
            "interpolation": interpolation,
        }

        for i in range(len(ramp.elements)):
            definitions[f"offset{i}"] = ramp.elements[i].position
            definitions[f"value{i}"] = list(ramp.elements[i].color[:3])  # Ignore alpha
    elif node.bl_idname == "ShaderNodeTexChecker":
        prefix = "scene.textures."

        # Note: Only "Object" texture coordinates are supported. Textured scale is not supported.
        scale = Matrix()
        for i in range(3):
            scale[i][i] = node.inputs["Scale"].default_value

        definitions = {
            "type": "checkerboard3d",
            "texture1": _socket(node.inputs["Color2"], props, obj_name, group_node),
            "texture2": _socket(node.inputs["Color1"], props, obj_name, group_node),
            "mapping.type": "localmapping3d",
            "mapping.transformation": utils.matrix_to_list(scale),
        }
    elif node.bl_idname == "ShaderNodeInvert":
        prefix = "scene.textures."

        fac_input = node.inputs["Fac"]
        fac = _socket(fac_input, props, obj_name, group_node)
        if fac_input.is_linked and fac == ERROR_VALUE:
            fac = 1

        tex = _socket(node.inputs["Color"], props, obj_name, group_node)

        if fac == 0:
            return tex

        definitions = {
            "type": "subtract",
            "texture1": 1,
            "texture2": tex,
        }

        if isinstance(fac, str) or (fac > 0 and fac < 1):
            # Here we need to insert a helper texture *after* the current texture
            props.Set(utils.create_props(prefix + luxcore_name + ".", definitions))
            definitions = {
                "type": "mix",
                "texture1": tex,
                "texture2": luxcore_name,
                "amount": fac,
            }
            luxcore_name = luxcore_name + "fac"
    elif node.bl_idname in {"ShaderNodeSeparateRGB", "ShaderNodeSeparateXYZ"}:
        prefix = "scene.textures."

        if node.bl_idname == "ShaderNodeSeparateRGB":
            channels = ["R", "G", "B"]
            tex_socket_name = "Image"
        else:
            channels = ["X", "Y", "Z"]
            tex_socket_name = "Vector"

        definitions = {
            "type": "splitfloat3",
            "texture": _socket(node.inputs[tex_socket_name], props, obj_name, group_node),
            "channel": channels.index(output_socket.name),
        }
    elif node.bl_idname in {"ShaderNodeCombineRGB", "ShaderNodeCombineXYZ"}:
        prefix = "scene.textures."

        definitions = {
            "type": "makefloat3",
            "texture1": _socket(node.inputs[0], props, obj_name, group_node),
            "texture2": _socket(node.inputs[1], props, obj_name, group_node),
            "texture3": _socket(node.inputs[2], props, obj_name, group_node),
        }
    else:
        LuxCoreErrorLog.add_warning(f"Unknown node type: {node.name}", obj_name=obj_name)

        # Try to skip this node by looking at its internal links (the same that are used when the node is muted)
        if node.internal_links:
            links = node.internal_links[0].from_socket.links
            if links:
                link = links[0]
                print("current node", node.name, "failed, testing next node:", link.from_node.name)
                return _node(link.from_node, link.from_socket, props, luxcore_name, obj_name, group_node)

        return ERROR_VALUE

    if node.bl_idname in {"ShaderNodeMixRGB", "ShaderNodeMath"} and node.use_clamp:
        # Here we need to insert a helper texture *after* the current texture
        props.Set(utils.create_props(prefix + luxcore_name + ".", definitions))
        definitions = {
            "type": "clamp",
            "texture": luxcore_name,
            "min": 0,
            "max": 1,
        }
        luxcore_name = luxcore_name + "clamp"

    props.Set(utils.create_props(prefix + luxcore_name + ".", definitions))
    return luxcore_name


def _squared_roughness_to_linear(socket, props, luxcore_name, obj_name, group_node):
    roughness = _socket(socket, props, obj_name, group_node)
    if socket.is_linked and roughness != ERROR_VALUE:
        # Implicitly create a math texture with unique name
        tex_name = luxcore_name + "roughness_converter"
        helper_prefix = "scene.textures." + tex_name + "."
        helper_defs = {
            "type": "power",
            "base": roughness,
            "exponent": 2,
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))
        return tex_name
    else:
        return roughness ** 2
