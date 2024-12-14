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

    result = _node(link.from_node, link.from_socket, props, material, luxcore_name, obj_name)
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


def _socket(socket, props, material, obj_name, group_node):
    link = utils_node.get_link(socket)
    if link:
        return _node(link.from_node, link.from_socket, props, material, None, obj_name, group_node)

    if not hasattr(socket, "default_value"):
        return ERROR_VALUE

    try:
        return list(socket.default_value)[:3]
    except TypeError:
        # Not iterable
        return socket.default_value


def _node(node, output_socket, props, material, luxcore_name=None, obj_name="", group_node_stack=None):
    if luxcore_name is None:
        luxcore_name = str(node.as_pointer()) + output_socket.name
        if group_node_stack:
            for n in group_node_stack:
                luxcore_name += str(n.as_pointer())
        luxcore_name = utils.sanitize_luxcore_name(luxcore_name)

    if node.bl_idname == "ShaderNodeBsdfPrincipled":
        prefix = "scene.materials."
        base_color = _socket(node.inputs["Base Color"], props, material, obj_name, group_node_stack)
        metallic_socket = node.inputs["Metallic"]
        metallic = _socket(metallic_socket, props, material, obj_name, group_node_stack)
        transmission_socket = node.inputs["Transmission"]
        transmission = _socket(transmission_socket, props, material, obj_name, group_node_stack)
        
        if transmission == 1 and metallic == 0:
            # It's effectively glass instead of a disney material.
            # Don't use mix for performance reasons.
            roughness = _squared_roughness_to_linear(node.inputs["Roughness"], props, material,
                                                     luxcore_name, obj_name, group_node_stack)

            definitions = {
                "type": "glass" if roughness == 0 else "roughglass",
                "kt": base_color,
                "kr": [1, 1, 1],
                "interiorior": _socket(node.inputs["IOR"], props, material, obj_name, group_node_stack),
            }

            if roughness != 0:
                definitions["uroughness"] = roughness
                definitions["vroughness"] = roughness
        else:
            definitions = {
                # TODO:
                #  - subsurface
                #  - clearcoat roughness (we have clearcoat gloss, probably need to invert or something)
                #  - clearcoat normal (no idea)
                #  - tangent (no idea)
                #  - transmission roughness (weird thing, might require rough glass + glossy coating?)
                "type": "disney",
                "basecolor": base_color,
                "subsurface": 0,  # TODO
                "metallic": metallic,
                "specular": _socket(node.inputs["Specular"], props, material, obj_name, group_node_stack),
                "speculartint": _socket(node.inputs["Specular Tint"], props, material, obj_name, group_node_stack),
                # Both LuxCore and Cycles use squared roughness here, no need to convert
                "roughness": _socket(node.inputs["Roughness"], props, material, obj_name, group_node_stack),
                "anisotropic": _socket(node.inputs["Anisotropic"], props, material, obj_name, group_node_stack),
                "sheen": _socket(node.inputs["Sheen"], props, material, obj_name, group_node_stack),
                "sheentint": _socket(node.inputs["Sheen Tint"], props, material, obj_name, group_node_stack),
                "clearcoat": _socket(node.inputs["Clearcoat"], props, material, obj_name, group_node_stack),
            }
            
            # Metallic values > 0 reduce transmission. At metallic = 1, no transmission happens at all
            if metallic != 1 and (transmission_socket.is_linked or transmission_socket.default_value > 0):
                luxcore_name_disney = luxcore_name + "_disney"
                props.Set(utils.create_props(prefix + luxcore_name_disney + ".", definitions))
                
                # Glass/Roughglass
                luxcore_name_glass = luxcore_name + "_glass"
                roughness = _squared_roughness_to_linear(node.inputs["Roughness"], props, material,
                                                         luxcore_name_glass, obj_name, group_node_stack)

                definitions = {
                    "type": "glass" if roughness == 0 else "roughglass",
                    "kt": base_color,
                    "kr": [1, 1, 1],
                    "interiorior": _socket(node.inputs["IOR"], props, material, obj_name, group_node_stack),
                }

                if roughness != 0:
                    definitions["uroughness"] = roughness
                    definitions["vroughness"] = roughness
                
                props.Set(utils.create_props(prefix + luxcore_name_glass + ".", definitions))
                
                # Calculate mix amount
                # metallic 1, transmission whatever -> mix_amount = 0
                # metallic 0, transmission whatever -> mix_amount = transmission
                # so: result = transmission * (1 - metallic)
                if _is_textured(metallic) or _is_textured(transmission):
                    if _is_textured(metallic):
                        inverted_metallic = luxcore_name + "inverted_metallic"
                        tex_prefix = "scene.textures." + inverted_metallic + "."
                        tex_definitions = {
                            "type": "subtract",
                            "texture1": 1,
                            "texture2": metallic,
                        }
                        props.Set(utils.create_props(tex_prefix, tex_definitions))
                    else:
                        inverted_metallic = 1 - metallic
                        
                    mix_amount = luxcore_name + "mix_amount"
                    tex_prefix = "scene.textures." + mix_amount + "."
                    tex_definitions = {
                        "type": "scale",
                        "texture1": inverted_metallic,
                        "texture2": transmission,
                    }
                    props.Set(utils.create_props(tex_prefix, tex_definitions))
                else:
                    mix_amount = transmission * (1 - metallic)
                
                # Mix
                definitions = {
                    "type": "mix",
                    "material1": luxcore_name_disney,
                    "material2": luxcore_name_glass,
                    "amount": mix_amount,
                }
        
        # Attach these props to the right-most material node (regardless if it's glass, disney or a mix mat)
        definitions.update({
            "emission": _socket(node.inputs["Emission"], props, material, obj_name, group_node_stack),
            "transparency": _socket(node.inputs["Alpha"], props, material, obj_name, group_node_stack),
            "bumptex": _socket(node.inputs["Normal"], props, material, obj_name, group_node_stack),
        })
    elif node.bl_idname == "ShaderNodeMixShader":
        prefix = "scene.materials."

        def convert_mat_socket(index):
            mat_name = _socket(node.inputs[index], props, material, obj_name, group_node_stack)
            if mat_name == ERROR_VALUE:
                mat_name, mat_props = black()
                props.Set(mat_props)
            return mat_name

        fac_input = node.inputs["Fac"]
        amount = _socket(fac_input, props, material, obj_name, group_node_stack)
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
            "kd": _socket(node.inputs["Color"], props, material, obj_name, group_node_stack),
            "bumptex": _socket(node.inputs["Normal"], props, material, obj_name, group_node_stack),
        }
    elif node.bl_idname == "ShaderNodeBsdfGlossy":
        prefix = "scene.materials."

        # Implicitly create a fresnelcolor texture with unique name
        tex_name = luxcore_name + "fresnel_helper"
        helper_prefix = "scene.textures." + tex_name + "."
        helper_defs = {
            "type": "fresnelcolor",
            "kr": _socket(node.inputs["Color"], props, material, obj_name, group_node_stack),
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))

        roughness = _squared_roughness_to_linear(node.inputs["Roughness"], props, material,
                                                 luxcore_name, obj_name, group_node_stack)

        definitions = {
            "type": "metal2",
            "fresnel": tex_name,
            "uroughness": roughness,
            "vroughness": roughness,
            "bumptex": _socket(node.inputs["Normal"], props, material, obj_name, group_node_stack),
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
                LuxCoreErrorLog.add_warning(error, obj_name=obj_name)
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
        color = _socket(node.inputs["Color"], props, material, obj_name, group_node_stack)
        roughness = _squared_roughness_to_linear(node.inputs["Roughness"], props, material,
                                                 luxcore_name, obj_name, group_node_stack)

        definitions = {
            "type": "glass" if roughness == 0 else "roughglass",
            "kt": color,
            "kr": color, # Nonsense, maybe leave white even if it breaks compatibility with Cycles?
            "interiorior": _socket(node.inputs["IOR"], props, material, obj_name, group_node_stack),
            "bumptex": _socket(node.inputs["Normal"], props, material, obj_name, group_node_stack),
        }

        if roughness != 0:
            definitions["uroughness"] = roughness
            definitions["vroughness"] = roughness
    elif node.bl_idname == "ShaderNodeBsdfRefraction":
        prefix = "scene.materials."
        color = _socket(node.inputs["Color"], props, material, obj_name, group_node_stack)
        roughness = _squared_roughness_to_linear(node.inputs["Roughness"], props, material,
                                                 luxcore_name, obj_name, group_node_stack)

        definitions = {
            "type": "glass" if roughness == 0 else "roughglass",
            "kt": color,
            "kr": [0, 0, 0],
            "interiorior": _socket(node.inputs["IOR"], props, material, obj_name, group_node_stack),
            "bumptex": _socket(node.inputs["Normal"], props, material, obj_name, group_node_stack),
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
            "kr": _socket(node.inputs["Color"], props, material, obj_name, group_node_stack),
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))

        # TODO emulate actual anisotropy and rotation somehow ...
        roughness = _squared_roughness_to_linear(node.inputs["Roughness"], props, material,
                                                 luxcore_name, obj_name, group_node_stack)

        definitions = {
            "type": "metal2",
            "fresnel": tex_name,
            "uroughness": roughness,
            "vroughness": 0.05,
            "bumptex": _socket(node.inputs["Normal"], props, material, obj_name, group_node_stack),
        }
    elif node.bl_idname == "ShaderNodeBsdfTranslucent":
        prefix = "scene.materials."
        definitions = {
            "type": "mattetranslucent",
            # TODO kt and kr don't really match Cycles result yet
            "kt": [1, 1, 1],
            "kr": _socket(node.inputs["Color"], props, material, obj_name, group_node_stack),
            "bumptex": _socket(node.inputs["Normal"], props, material, obj_name, group_node_stack),
        }
    elif node.bl_idname == "ShaderNodeBsdfTransparent":
        prefix = "scene.materials."
        definitions = {
            "type": "null",
        }
        color = _socket(node.inputs["Color"], props, material, obj_name, group_node_stack)
        if color != 1 and color != [1, 1, 1]:
            definitions["transparency"] = color
    elif node.bl_idname == "ShaderNodeHoldout":
        prefix = "scene.materials."
        definitions = {
            "type": "matte",
            "kd": [0, 0, 0],
            "holdout.enable": True,
        }
    elif node.bl_idname == "ShaderNodeMixRGB":
        # TODO (in LuxCore):
        #  "DARKEN", "BURN", "LIGHTEN", "SCREEN", "DODGE", "OVERLAY", "SOFT_LIGHT",
        #  "LINEAR_LIGHT", "DIFFERENCE", "HUE", "SATURATION", "COLOR", "VALUE"

        prefix = "scene.textures."
        definitions = {}

        fac_input = node.inputs["Fac"]
        fac = _socket(fac_input, props, material, obj_name, group_node_stack)
        if fac_input.is_linked and fac == ERROR_VALUE:
            fac = 0.5

        tex1 = _socket(node.inputs["Color1"], props, material, obj_name, group_node_stack)
        tex2 = _socket(node.inputs["Color2"], props, material, obj_name, group_node_stack)

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
            LuxCoreErrorLog.add_warning(f"Unsupported MixRGB mode: {blend_type}", obj_name=obj_name)
            return ERROR_VALUE

        if (_is_textured(fac) or (fac > 0 and fac < 1)) and blend_type != "MIX":
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

        tex1 = _socket(node.inputs[0], props, material, obj_name, group_node_stack)
        tex2 = _socket(node.inputs[1], props, material, obj_name, group_node_stack)

        # In Cycles, the inputs are converted to float values (e.g. averaged in case of RGB input).
        # The following LuxCore textures would perform RGB operations if we didn't convert the inputs to floats.
        if node.operation in {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "ABSOLUTE"}:
            tex1 = _convert_to_float(tex1, props)
            tex2 = _convert_to_float(tex2, props)

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
            LuxCoreErrorLog.add_warning(f"Unsupported Math mode: {node.operation}", obj_name=obj_name)
            return ERROR_VALUE
    elif node.bl_idname == "ShaderNodeHueSaturation":
        prefix = "scene.textures."

        hue = _socket(node.inputs["Hue"], props, material, obj_name, group_node_stack)
        saturation = _socket(node.inputs["Saturation"], props, material, obj_name, group_node_stack)
        value = _socket(node.inputs["Value"], props, material, obj_name, group_node_stack)
        fac = _socket(node.inputs["Fac"], props, material, obj_name, group_node_stack)  # TODO
        color = _socket(node.inputs["Color"], props, material, obj_name, group_node_stack)

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
        
        if group_node_stack is None:
            _group_node_stack = []
        else:
            _group_node_stack = group_node_stack.copy()
        
        _group_node_stack.append(node)
        
        # I call _node instead of _socket here because I need to pass the
        # luxcore_name in case the node group is the first node in the tree
        return _node(link.from_node, link.from_socket, props, material, luxcore_name, obj_name, _group_node_stack)
    elif node.bl_idname == "NodeGroupInput":
        return _socket(group_node_stack[-1].inputs[output_socket.name], props, material, obj_name, group_node_stack[:-1])
    elif node.bl_idname == "ShaderNodeEmission":
        prefix = "scene.materials."

        color = _socket(node.inputs["Color"], props, material, obj_name, group_node_stack)
        # According to the Blender manual, strength is in Watts/m² when the node is used on meshes.
        strength = _socket(node.inputs["Strength"], props, material, obj_name, group_node_stack)

        emission_col = luxcore_name + "emission_col"
        helper_prefix = "scene.textures." + emission_col + "."
        helper_defs = {
            "type": "scale",
            "texture1": strength,
            "texture2": color,
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))

        definitions = {
            "type": "matte",
            "kd": [0, 0, 0],
            "emission": emission_col,
            "emission.gain": [1] * 3,
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
            "amount": _socket(node.inputs["Fac"], props, material, obj_name, group_node_stack),
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
            "texture1": _socket(node.inputs["Color2"], props, material, obj_name, group_node_stack),
            "texture2": _socket(node.inputs["Color1"], props, material, obj_name, group_node_stack),
            "mapping.type": "localmapping3d",
            "mapping.transformation": utils.matrix_to_list(scale),
        }
    elif node.bl_idname == "ShaderNodeInvert":
        prefix = "scene.textures."

        fac_input = node.inputs["Fac"]
        fac = _socket(fac_input, props, material, obj_name, group_node_stack)
        if fac_input.is_linked and fac == ERROR_VALUE:
            fac = 1

        tex = _socket(node.inputs["Color"], props, material, obj_name, group_node_stack)

        if fac == 0:
            return tex

        definitions = {
            "type": "subtract",
            "texture1": 1,
            "texture2": tex,
        }

        if _is_textured(fac) or (fac > 0 and fac < 1):
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
            "texture": _socket(node.inputs[tex_socket_name], props, material, obj_name, group_node_stack),
            "channel": channels.index(output_socket.name),
        }
    elif node.bl_idname in {"ShaderNodeCombineRGB", "ShaderNodeCombineXYZ"}:
        prefix = "scene.textures."

        definitions = {
            "type": "makefloat3",
            "texture1": _socket(node.inputs[0], props, material, obj_name, group_node_stack),
            "texture2": _socket(node.inputs[1], props, material, obj_name, group_node_stack),
            "texture3": _socket(node.inputs[2], props, material, obj_name, group_node_stack),
        }
    elif node.bl_idname == "ShaderNodeRGBToBW":
        prefix = "scene.textures."

        definitions = {
            "type": "dotproduct",
            "texture1": _socket(node.inputs["Color"], props, material, obj_name, group_node_stack),
            # From Cycles source code:
            # intern/cycles/render/shader.cpp:726: float ShaderManager::linear_rgb_to_gray(float3 c)
            "texture2": [0.2126729, 0.7151522, 0.0721750],
        }
    elif node.bl_idname == "ShaderNodeBrightContrast":
        prefix = "scene.textures."

        definitions = {
            "type": "brightcontrast",
            "texture": _socket(node.inputs["Color"], props, material, obj_name, group_node_stack),
            "brightness": _socket(node.inputs["Bright"], props, material, obj_name, group_node_stack),
            "contrast": _socket(node.inputs["Contrast"], props, material, obj_name, group_node_stack),
        }
    elif node.bl_idname == "ShaderNodeGamma":
        #print(f"ShaderNodeGamma inputs: {[input.name for input in node.inputs]}")

        prefix = "scene.textures."

        # Check if the Gamma node input is a Texture Image node
        texture_input = utils_node.get_link(node.inputs["Color"])
        if texture_input and texture_input.from_node.bl_idname == "ShaderNodeTexImage":
            tex_node = texture_input.from_node
        
            # Extract the image filepath and gamma value
            gamma_value = _socket(node.inputs["Gamma"], props, material, obj_name, group_node_stack)

            if not gamma_value:
                gamma_value = 1  # Default to 1 if no value is provided
        
            filepath = ImageExporter.export_cycles_node_reader(tex_node.image)
            extension_map = {
                "REPEAT": "repeat",
                "EXTEND": "clamp",
                "CLIP": "black",
            }
        
            definitions = {
                "type": "imagemap",
                "file": filepath,
                "wrap": extension_map.get(tex_node.extension, "repeat"),
                "gamma": gamma_value,
                "gain": 1,  # Adjust as necessary
                "mapping.type": "uvmapping2d",
                "mapping.uvscale": [1, -1],
                "mapping.rotation": 0,
                "mapping.uvdelta": [0, 1],
            }
        
            # Define the LuxCore texture node
            props.Set(utils.create_props(prefix + luxcore_name + ".", definitions))
            return luxcore_name

    elif node.bl_idname == "ShaderNodeNormalMap":
        if node.space != "TANGENT":
            LuxCoreErrorLog.add_warning(f"Unsupported normal map space: {node.space}", obj_name=obj_name)
            return ERROR_VALUE

        prefix = "scene.textures."

        definitions = {
            "type": "normalmap",
            "texture": _socket(node.inputs["Color"], props, material, obj_name, group_node_stack),
        }

        strength_socket = node.inputs["Strength"]
        if strength_socket.is_linked:
            # Use scale texture because normalmap scale can't be textured
            # Here we need to insert a helper texture *after* the current texture
            props.Set(utils.create_props(prefix + luxcore_name + ".", definitions))
            definitions = {
                "type": "scale",
                "texture1": luxcore_name,
                "texture2": _socket(strength_socket, props, material, obj_name, group_node_stack),
            }
            luxcore_name = luxcore_name + "strength"
        else:
            definitions["scale"] = strength_socket.default_value
    elif node.bl_idname == "ShaderNodeBump":
        if node.inputs["Distance"].is_linked:
            LuxCoreErrorLog.add_warning("Bump node Distance socket is not supported", obj_name=obj_name)
        if node.inputs["Normal"].is_linked:
            LuxCoreErrorLog.add_warning("Bump node Normal socket is not supported", obj_name=obj_name)

        prefix = "scene.textures."

        definitions = {
            "type": "scale",
            "texture1": _socket(node.inputs["Height"], props, material, obj_name, group_node_stack),
            "texture2": _socket(node.inputs["Strength"], props, material, obj_name, group_node_stack),
        }

        if node.invert:
            props.Set(utils.create_props(prefix + luxcore_name + ".", definitions))
            definitions = {
                "type": "scale",
                "texture1": luxcore_name,
                "texture2": -1,
            }
            luxcore_name = luxcore_name + "invert"
    elif node.bl_idname == "ShaderNodeNewGeometry":
        prefix = "scene.textures."
        definitions = {}
        
        # TODO: when support for pointiness and random per island is added, we have to:
        #  - make sure the necessary shapes are added during object export
        #  - make sure the mesh is re-exported when one of these outputs is used the first time during viewport render, 
        #    otherwise we crash LuxCore in case of random per island, or the feature doesn't work in case of pointiness
        if output_socket.name == "Position":
            definitions["type"] = "position"
        elif output_socket.name == "Normal":
            definitions["type"] = "shadingnormal"
        else:
            LuxCoreErrorLog.add_warning(f"Unsupported Geometry output socket: {output_socket.name}", obj_name=obj_name)
            return ERROR_VALUE
    elif node.bl_idname == "ShaderNodeObjectInfo":
        prefix = "scene.textures."
        definitions = {}
        
        if output_socket.name == "Object Index":
            definitions["type"] = "objectid"
        elif output_socket.name == "Material Index":
            definitions["type"] = "constfloat1"
            definitions["value"] = material.pass_index
        elif output_socket.name == "Random":
            definitions["type"] = "objectidnormalized"
        else:
            LuxCoreErrorLog.add_warning(f"Unsupported Object Info output socket: {output_socket.name}", obj_name=obj_name)
            return ERROR_VALUE
    elif node.bl_idname == "ShaderNodeBlackbody":
        temperature_socket = node.inputs["Temperature"]
        if temperature_socket.is_linked:
            LuxCoreErrorLog.add_warning(f"LuxCore does not support textured blackbody temperature", obj_name=obj_name)
            return ERROR_VALUE
        
        prefix = "scene.textures."
        
        definitions = {
            "type": "blackbody",
            "temperature": temperature_socket.default_value,
            "normalize": True,
        }
    elif node.bl_idname == "ShaderNodeMapRange":
        if node.interpolation_type != "LINEAR":
            LuxCoreErrorLog.add_warning(f"In material {material.name}: Unsupported map range interpolation type: " + node.interpolation_type,
                                        obj_name=obj_name)
            return ERROR_VALUE

        if not node.clamp:
            # TODO: LuxCore's remap texture always clamps, at the moment
            LuxCoreErrorLog.add_warning(f"In material {material.name}: map range node will be clamped", obj_name=obj_name)

        prefix = "scene.textures."

        value = _socket(node.inputs["Value"], props, material, obj_name, group_node_stack)
        value = _convert_to_float(value, props)

        definitions = {
            "type": "remap",
            "value": value,
            "sourcemin": _socket(node.inputs["From Min"], props, material, obj_name, group_node_stack),
            "sourcemax": _socket(node.inputs["From Max"], props, material, obj_name, group_node_stack),
            "targetmin": _socket(node.inputs["To Min"], props, material, obj_name, group_node_stack),
            "targetmax": _socket(node.inputs["To Max"], props, material, obj_name, group_node_stack),
        }
    else:
        LuxCoreErrorLog.add_warning(f"Unsupported node type: {node.name}", obj_name=obj_name)

        # TODO do this for unsupported mixRGB and math modes, too
        # Try to skip this node by looking at its internal links (the same that are used when the node is muted)
        if node.internal_links:
            links = node.internal_links[0].from_socket.links
            if links:
                link = links[0]
                print("current node", node.name, "failed, testing next node:", link.from_node.name)
                return _node(link.from_node, link.from_socket, props, material, luxcore_name, obj_name, group_node_stack)

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


def _squared_roughness_to_linear(socket, props, material, luxcore_name, obj_name, group_node):
    roughness = _socket(socket, props, material, obj_name, group_node)
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


def _is_textured(value):
    return isinstance(value, str)


def _convert_to_float(color_or_texture, props):
    if _is_textured(color_or_texture):
        # This is more or less a hack because we don't have a dedicated "RGB to BW" texture
        tex_name = color_or_texture + "to_float"
        helper_prefix = "scene.textures." + tex_name + "."
        helper_defs = {
            "type": "power",
            "base": color_or_texture,
            "exponent": 1,
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))
        return tex_name
    elif isinstance(color_or_texture, list):
        return sum(color_or_texture) / len(color_or_texture)
