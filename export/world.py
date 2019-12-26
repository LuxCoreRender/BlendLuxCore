from ..bin import pyluxcore
from .. import utils
from ..nodes.output import get_active_output
from . import light
from ..utils.errorlog import LuxCoreErrorLog
from ..utils import node as utils_node
from mathutils import Matrix

WORLD_BACKGROUND_LIGHT_NAME = "__WORLD_BACKGROUND_LIGHT__"

# TODO: currently it is not possible to remove the world volume during viewport render

def convert_cycles_settings(exporter, depsgraph, scene, is_viewport_render):
    world = scene.world

    luxcore_name = WORLD_BACKGROUND_LIGHT_NAME
    lightgroup_id = scene.luxcore.lightgroups.get_id_by_name(world.luxcore.lightgroup)
    exporter.lightgroup_cache.add(lightgroup_id)

    prefix = "scene.lights." + luxcore_name + "."
    definitions = {}

    definitions["importance"] = world.luxcore.importance
    definitions["id"] = lightgroup_id

    if world.use_nodes:
        if world.node_tree:
            error = False
            output = world.node_tree.get_output_node("CYCLES")
            if output is None:
                error = True
            else:
                link = utils_node.get_link(output.inputs["Surface"])
                if link is None:
                    error = True
                else:
                    node = link.from_node

                    if node.bl_idname == "ShaderNodeBackground":
                        if node.inputs["Color"].is_linked:
                            colornode = node.inputs['Color'].links[0].from_node
                            name = colornode.bl_idname

                            if name == "ShaderNodeTexSky":
                                if colornode.sky_type == "HOSEK_WILKIE":
                                    definitions["type"] = "sky2"
                                    definitions["dir"] = list(colornode.sun_direction)
                                    definitions["turbidity"] = colornode.turbidity
                                    definitions["groundalbedo"] = [colornode.ground_albedo*x for x in [1, 1, 1]]
                                    gain = node.inputs["Strength"].default_value
                                    #Adjust gain to match cycles sky intensity
                                    definitions["gain"] = [0.00002*gain * x for x in [1, 1, 1]]

                                else:
                                    LuxCoreErrorLog.add_warning(
                                        f"Unsupported sky type: Only HOSEK_WILKIE is supported: {node.name}",
                                        obj_name=luxcore_name)

                            elif name == "ShaderNodeTexEnvironment" and colornode.image:
                                definitions["type"] = "infinite"
                                definitions["file"] = colornode.image.filepath
                                #TODO: Implement other color spaces (cycles colorspace input)
                                definitions["gamma"] = 1.0

                                infinite_fix = Matrix.Scale(1.0, 4)
                                infinite_fix[0][0] = -1.0  # mirror the hdri map to match Cycles and old LuxBlend
                                
                                #TODO: Implement transformation (vector input from cycles)
                                transformation = utils.matrix_to_list(infinite_fix)
                                definitions["transformation"] = transformation

                            elif name == "ShaderNodeRGB":
                                definitions["type"] = "constantinfinite"
                                gain = node.inputs["Strength"].default_value
                                # Adjust gain to match cycles sky intensity
                                definitions["gain"] = [gain * x for x in [0.0001, 0.0001, 0.0001]]
                                definitions["color"] = list(colornode.outputs["Color"].default_value)[:3]
                            else:
                                # TODO: Add support for further constant float/color nodes
                                # Fallback light
                                definitions["type"] = "constantinfinite"
                                LuxCoreErrorLog.add_warning(
                                    f"Unsupported setup: Input socket is linked: {node.name}",
                                    obj_name=luxcore_name)
                        else:
                            definitions["type"] = "constantinfinite"
                            definitions["color"] = list(node.inputs["Color"].default_value)[:3]

                        if node.inputs["Strength"].is_linked:
                            # TODO: Add support for linked strength socket in case of constant float nodes
                            LuxCoreErrorLog.add_warning(
                                f"Unsupported setup: Input socket 'Strength' is linked: {node.name}",
                                obj_name=luxcore_name)
                        else:
                            gain = node.inputs["Strength"].default_value
                            definitions["gain"] = [gain*x  for x in [1, 1, 1]]

                    else:
                        LuxCoreErrorLog.add_warning(f"Unsupported node type: {node.name}", obj_name=luxcore_name)
            if error:
                definitions["color"] = [0, 0, 0]
                msg = 'World "%s": %s' % (world.name, "Could not convert node tree")
                LuxCoreErrorLog.add_warning(msg)
        else:
            msg = 'World "%s": %s' % (world.name, "No node tree found")
            LuxCoreErrorLog.add_warning(msg)


    else:
        # Adjust gain to 0.75 to match color of cycles background intensity
        definitions["gain"] = [0.75, 0.75, 0.75]
        definitions["color"] = [x for x in world.color]

    props = utils.create_props(prefix, definitions)
    return props


def convert_luxcore_settings(exporter, depsgraph, scene, is_viewport_render):
    props = pyluxcore.Properties()
    world = scene.world

    # World light (this is a BlendLuxCore concept)
    if world.luxcore.light != "none":
        world_light_props = light.convert_world(exporter, world, scene, is_viewport_render)
        props.Set(world_light_props)

    # World volume
    volume_node_tree = world.luxcore.volume

    if volume_node_tree:
        luxcore_name = utils.get_luxcore_name(volume_node_tree)
        active_output = get_active_output(volume_node_tree)
        try:
            active_output.export(exporter, depsgraph, props, luxcore_name)
            props.Set(pyluxcore.Property("scene.world.volume.default", luxcore_name))
        except Exception as error:
            msg = 'World "%s": %s' % (world.name, error)
            LuxCoreErrorLog.add_warning(msg)
    return props


def convert(exporter, depsgraph, scene, is_viewport_render):
    props = pyluxcore.Properties()
    world = scene.world

    if not world:
        return props

    if world.luxcore.use_cycles_settings:
        props = convert_cycles_settings(exporter, depsgraph, scene, is_viewport_render)
    else:
        props = convert_luxcore_settings(exporter, depsgraph, scene, is_viewport_render)
    return props
