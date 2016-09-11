import bpy
from ..bin import pyluxcore


class CacheEntry(object):
    def __init__(self, luxcore_names, props):
        self.luxcore_names = luxcore_names
        self.props = props
        self.is_updated = True  # new entries are flagged as updated


class Cache(object):
    _cache = {}

    @classmethod
    def get_entry(cls, datablock):
        if type(datablock) == bpy.types.Object:
            if datablock.type in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'EMPTY'):
                convert_func = convert_object
            elif datablock.type == 'LAMP':
                convert_func = convert_light
            elif datablock.type == 'CAMERA':
                convert_func = convert_camera
            else:
                raise Exception("Can not convert object type:", datablock.type)
        else:
            raise Exception("Can not convert datablock type:", type(datablock))

        key = make_key(datablock)
        if key not in cls._cache or datablock.is_updated:
            cls._cache[key] = convert_func(datablock)
        else:
            # Entry was not updated
            cls._cache[key].is_updated = False

        return cls._cache[key]


def make_key(datablock):
    key = datablock.name
    if datablock.library:
        key += datablock.library.name
    return key


def convert_object(datablock):
    print("converting object:", datablock.name)
    props = pyluxcore.Properties()

    props.Set(pyluxcore.Property("scene.materials.test.type", "matte"))
    props.Set(pyluxcore.Property("scene.materials.test.kd", [0.0, 0.7, 0.7]))

    props.Set(pyluxcore.Property("scene.objects.test.material", "test"))
    props.Set(pyluxcore.Property("scene.objects.test.ply", "F:\\Users\\Simon_2\\Downloads\\untitled.ply"))
    props.Set(pyluxcore.Property("scene.objects.test.transformation", matrix_to_list(datablock.matrix_world)))

    return CacheEntry(["test"], props)


def convert_light(datablock):
    print("converting light")
    return CacheEntry(["testlight1", "testlight2"], pyluxcore.Properties())


def convert_camera(datablock):
    print("converting camera")
    return CacheEntry([], pyluxcore.Properties())


def matrix_to_list(matrix, apply_worldscale=False, invert=False):
    """
    Flatten a 4x4 matrix into a list
    Returns list[16]
    """

    if apply_worldscale:
        matrix = matrix.copy()
        sm = get_worldscale()
        matrix *= sm
        ws = get_worldscale(as_scalematrix=False)
        matrix[0][3] *= ws
        matrix[1][3] *= ws
        matrix[2][3] *= ws

    if invert:
        matrix = matrix.inverted()

    l = [matrix[0][0], matrix[1][0], matrix[2][0], matrix[3][0],
         matrix[0][1], matrix[1][1], matrix[2][1], matrix[3][1],
         matrix[0][2], matrix[1][2], matrix[2][2], matrix[3][2],
         matrix[0][3], matrix[1][3], matrix[2][3], matrix[3][3]]

    return [float(i) for i in l]
