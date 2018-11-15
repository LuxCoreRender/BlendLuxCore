from time import time
from .. import utils
import array


def convert(smoke_obj, channel):
    start = time()

    # Search smoke domain target for smoke modifiers
    smoke_domain_mod = utils.find_smoke_domain_modifier(smoke_obj)

    if smoke_domain_mod is None:
        msg = 'Object "%s" is not a smoke domain' % smoke_obj.name
        raise Exception(msg)

    settings = smoke_domain_mod.domain_settings

    if channel == "density":
        grid = settings.density_grid
    elif channel == "fire":
        grid = settings.flame_grid
    elif channel == "heat":
        grid = settings.heat_grid
    elif channel == "color":
        grid = settings.color_grid
    elif channel == "velocity":
        grid = settings.velocity_grid
    else:
        raise NotImplementedError("Unknown channel type " + channel)

    # Prevent a crash
    if len(grid) == 0:
        msg = 'Object "%s": No smoke data (simulate some frames first)' % smoke_obj.name
        raise Exception(msg)

    # We have to convert Blender's bpy_prop_array because it doesn't support the Python buffer interface.
    # We use an array instead of a list here to save a lot of memory (list would use doubles instead of floats).
    channeldata = array.array("f", grid)

    # The smoke resolution along the x, y, z axis
    resolution = list(settings.domain_resolution)

    # Note: Velocity and heat data is always low-resolution. (Comment from Cycles source code)
    if settings.use_high_resolution and channel not in {"velocity", "heat"}:
        for i in range(3):
            resolution[i] *= settings.amplify + 1

    print("conversion to array took %.3f s" % (time() - start))

    return resolution, channeldata
