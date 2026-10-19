import bpy
import os
import pyluxcore
from .. import utils
from ..utils.node import get_active_output
from . import light
from ..utils.errorlog import LuxCoreErrorLog

# TODO: currently it is not possible to remove the world volume during viewport render


def convert(exporter, depsgraph, scene, is_viewport_render):
    props = pyluxcore.Properties()
    world = scene.world

    # Prague Sky Model atmosphere parameters, shared by all sky3/sun3 lights of the scene
    praguesky_props = _convert_pragueskymodel(scene)
    if praguesky_props:
        props.Set(praguesky_props)

    if not world:
        return props

    # World light (this is a BlendLuxCore concept)
    world_light_props = light.convert_world(exporter, world, scene, is_viewport_render)
    if world_light_props:
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


def _needs_pragueskymodel(scene):
    """True if the scene contains sky3/sun3 lights that use the Prague Sky Model."""
    world = scene.world
    if world and not world.luxcore.use_cycles_settings and world.luxcore.light == "sky3":
        return True

    for obj in scene.objects:
        if (obj.type == "LIGHT" and obj.data and obj.data.type == "SUN"
                and obj.data.luxcore.light_type == "sun3"):
            return True

    return False


def _convert_pragueskymodel(scene):
    """
    Export the scene.pragueskymodel.* block with the dataset path and the
    atmosphere parameters shared by all sky3/sun3 lights of the scene.
    """
    if not _needs_pragueskymodel(scene):
        return None

    definitions = {}

    world = scene.world
    if world and not world.luxcore.use_cycles_settings and world.luxcore.light == "sky3":
        definitions["visibility"] = world.luxcore.sky3_visibility
        definitions["altitude"] = world.luxcore.sky3_altitude
        definitions["groundalbedo"] = world.luxcore.sky3_groundalbedo

    # The dataset path is an addon preference
    prefs = utils.get_addon_preferences(bpy.context)
    dataset_path = bpy.path.abspath(prefs.skymodel_dataset_path)
    if dataset_path:
        if os.path.isfile(dataset_path):
            definitions["dataset"] = dataset_path
        else:
            LuxCoreErrorLog.add_warning(
                'Prague Sky Model dataset not found: "%s" '
                "(set the correct path in the addon preferences)" % dataset_path)
    # If no path is set, LuxCore resolves the default file name "SkyModelDataset.dat"

    return utils.luxutils.create_props("scene.pragueskymodel.", definitions)
