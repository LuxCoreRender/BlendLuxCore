from .. import utils
import array


def convert(smoke_obj, channel):
    from time import time
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
    # ToDo: implement velocity grid export
    # velocity grid has 3 times more values => probably vector field
    #elif channel == "velocity":
    #    grid = settings.velocity_grid
    else:
        raise NotImplementedError("Unknown channel type " + channel)

    # Prevent a crash
    if len(grid) == 0:
        msg = 'Object "%s": No smoke data (simulate some frames first)' % smoke_obj.name
        raise Exception(msg)

    channeldata = list(grid)

    if channel == "color":
        # Delete every 4th element because the color_grid contains 4 values per cell
        # but LuxCore expects 3 values per cell (r, g, b)
        del channeldata[3::4]

    # The smoke resolution along the x, y, z axis
    resolution = list(settings.domain_resolution)

    # Note: Velocity and heat data is always low-resolution. (Comment from Cycles source code)
    if settings.use_high_resolution and channel not in {"velocity", "heat"}:
        for i in range(3):
            resolution[i] *= settings.amplify + 1

    print("conversion to list took %.3fs" % (time() - start))

    return resolution[0], resolution[1], resolution[2], channeldata
