from ..bin import pyluxcore
from .. import utils
from . import CacheEntry

def convert(datablock):
    print("converting object:", datablock.name)
    luxcore_name = utils.to_luxcore_name(datablock.name)
    props = pyluxcore.Properties()

    props.Set(pyluxcore.Property("scene.materials.test.type", "matte"))
    props.Set(pyluxcore.Property("scene.materials.test.kd", [0.0, 0.7, 0.7]))

    props.Set(pyluxcore.Property("scene.objects." + luxcore_name + ".material", "test"))
    props.Set(pyluxcore.Property("scene.objects." + luxcore_name + ".ply", "F:\\Users\\Simon_2\\Downloads\\untitled.ply"))
    props.Set(pyluxcore.Property("scene.objects." + luxcore_name + ".transformation", utils.matrix_to_list(datablock.matrix_world)))

    return props