from ..bin import pyluxcore
from ..utils import matrix_to_list
from . import CacheEntry

def convert(datablock):
    print("converting object:", datablock.name)
    props = pyluxcore.Properties()

    # props.Set(pyluxcore.Property("scene.materials.test.type", "matte"))
    # props.Set(pyluxcore.Property("scene.materials.test.kd", [0.0, 0.7, 0.7]))
    #
    # props.Set(pyluxcore.Property("scene.objects.test.material", "test"))
    # props.Set(pyluxcore.Property("scene.objects.test.ply", "F:\\Users\\Simon_2\\Downloads\\untitled.ply"))
    # props.Set(pyluxcore.Property("scene.objects.test.transformation", matrix_to_list(datablock.matrix_world)))

    return CacheEntry(["test"], props)