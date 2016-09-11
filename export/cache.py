import bpy
from ..bin import pyluxcore
from . import blender_object
from . import camera
from . import make_key


class Cache(object):
    _cache = {}
    _luxcore_session = None
    _session_locked = False

    @classmethod
    def get_entry(cls, datablock):
        if type(datablock) == bpy.types.Object:
            if datablock.type in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'EMPTY'):
                convert = blender_object.convert
            elif datablock.type == 'LAMP':
                convert = convert_light  # TODO
            elif datablock.type == 'CAMERA':
                # TODO: I don't think we need to handle cameras here. After all, there's only one active camera at a time
                # better have explicit camera update outside of the cache
                convert = camera.convert
            else:
                raise Exception("Can not convert object type:", datablock.type)
        else:
            raise Exception("Can not convert datablock type:", type(datablock))

        key = make_key(datablock)
        if key not in cls._cache or datablock.is_updated:
            cls._cache[key] = convert(datablock)
        else:
            # Entry was not updated
            cls._cache[key].is_updated = False

        return cls._cache[key]

    @classmethod
    def get_session(cls):
        if cls._session_locked:
            # Another viewport/finalrender holds the session lock
            print("session already locked")
            return None

        if cls._luxcore_session is None:
            cls._start_session()

        cls._session_locked = True
        return cls._luxcore_session

    @classmethod
    def stop_session(cls):
        # TODO what about the lock? (and maybe check if running, if in sceneedit etc.)
        if cls._luxcore_session:
            print("stopping luxcore session")
            cls._luxcore_session.Stop()
            cls._luxcore_session = None
        else:
            print("ERROR: no running luxcore session")

    @classmethod
    def _start_session(cls):
        print("starting luxcore session")

