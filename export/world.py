from ..bin import pyluxcore
from .. import utils
from ..nodes.output import get_active_output
from . import light

# TODO: currently it is not possible to remove the world volume during viewport render


def convert(exporter, scene):
    props = pyluxcore.Properties()
    world = scene.world

    if not world:
        return props

    # World light (this is a BlendLuxCore concept)
    if world.luxcore.light != "none":
        world_light_props = light.convert_world(exporter, world, scene)
        props.Set(world_light_props)

    # World volume
    volume_node_tree = world.luxcore.volume

    if volume_node_tree:
        luxcore_name = utils.get_luxcore_name(volume_node_tree)
        active_output = get_active_output(volume_node_tree)
        try:
            active_output.export(exporter, props, luxcore_name)
            props.Set(pyluxcore.Property("scene.world.volume.default", luxcore_name))
        except Exception as error:
            msg = 'World "%s": %s' % (world.name, error)
            scene.luxcore.errorlog.add_warning(msg)

    return props
