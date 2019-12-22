from ..bin import pyluxcore
from .. import utils
from ..nodes.output import get_active_output
from . import light
from ..utils.errorlog import LuxCoreErrorLog

WORLD_BACKGROUND_LIGHT_NAME = "__WORLD_BACKGROUND_LIGHT__"

# TODO: currently it is not possible to remove the world volume during viewport render

def convert_cycles_settings(exporter, depsgraph, scene, is_viewport_render):
    world = scene.world

    luxcore_name = WORLD_BACKGROUND_LIGHT_NAME
    lightgroup_id = scene.luxcore.lightgroups.get_id_by_name(world.luxcore.lightgroup)
    exporter.lightgroup_cache.add(lightgroup_id)

    prefix = "scene.lights." + luxcore_name + "."
    definitions = {}

    definitions["type"] = "constantinfinite"
    definitions["importance"] = world.luxcore.importance
    definitions["id"] = lightgroup_id

    if world.use_nodes:
        #TODO: Implement node tree export
        print("Not implemented yet")
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
