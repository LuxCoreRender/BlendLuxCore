from ..bin import pyluxcore
from . import CacheEntry


def needs_update():
    # TODO (store info in cache or so? and rely on cam_obj.is_updated for stuff like special parameters?)
    return True


def convert(scene, context=None):
    print("converting camera")
    props = pyluxcore.Properties()

    # TODO

    return props