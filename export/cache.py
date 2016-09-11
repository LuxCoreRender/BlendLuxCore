import bpy
from ..bin import pyluxcore
from . import blender_object
from . import camera
from . import make_key

class Cache(object):
    _cache = {}

    @classmethod
    def get_entry(cls, datablock):
        if type(datablock) == bpy.types.Object:
            if datablock.type in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'EMPTY'):
                convert_func = blender_object.convert
            elif datablock.type == 'LAMP':
                convert_func = convert_light  # TODO
            elif datablock.type == 'CAMERA':
                convert_func = camera.convert
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