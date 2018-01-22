import bpy
from .. import utils
from time import time

def convert(smoke_obj, channel):
    print("[%s] Beginning smoke export (channel: %s)" % (smoke_obj.name, channel))
    start_time = time()

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
    big_res = list(settings.domain_resolution)

    if settings.use_high_resolution:
        for i in range(3):
            big_res[i] *= settings.amplify + 1

    elapsed_time = time() - start_time
    print("[%s] Smoke export of channel %s took %.3fs" % (smoke_obj.name, channel, elapsed_time))

    return big_res[0], big_res[1], big_res[2], channeldata
