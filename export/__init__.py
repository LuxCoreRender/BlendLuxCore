import bpy


class CacheEntry(object):
    def __init__(self, luxcore_names, props):
        self.luxcore_names = luxcore_names
        self.props = props
        self.is_updated = True  # new entries are flagged as updated


def make_key(datablock):
    key = datablock.name
    if datablock.library:
        key += datablock.library.name
    return key


# def convert_light(datablock):
#     print("converting light")
#     return CacheEntry(["testlight1", "testlight2"], pyluxcore.Properties())
