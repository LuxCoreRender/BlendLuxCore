from ..bin import pyluxcore
from . import CacheEntry

def convert(datablock):
    print("converting camera")
    return CacheEntry([], pyluxcore.Properties())