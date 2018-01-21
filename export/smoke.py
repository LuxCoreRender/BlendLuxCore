import bpy
from ..bin import pyluxcore
from .. import utils
from . import blender_object
from time import time
from array import array
from . import caches

def convert(smoke_obj, channel):
    print("[%s] Beginning smoke export (channel: %s)" % (smoke_obj.name, channel))
    start_time = time()

    domain = None

    # Search smoke domain target for smoke modifiers
    for mod in smoke_obj.modifiers:
        if mod.name == "Smoke":
            if mod.smoke_type == "DOMAIN":
                domain = smoke_obj
                break
    
    if domain is not None:
        settings = mod.domain_settings

        if channel == "density":
            channeldata = list(settings.density_grid)
        elif channel == "fire":
            channeldata = list(settings.flame_grid)
        elif channel == "heat":
            channeldata = list(settings.heat_grid)
        # ToDo: implement velocity grid export
        # velocity grid has 3 times more values => probably vector field
        #elif channel == "velocity":
        #    channeldata = list(settings.velocity_grid)

        big_res = list(settings.domain_resolution)

        if settings.use_high_resolution:
            for i in range(3):
                big_res[i] *= settings.amplify + 1                    

    elapsed_time = time() - start_time
    print("[%s] Smoke export of channel %s took %.3fs" % (smoke_obj.name, channel, elapsed_time))

    return big_res[0], big_res[1], big_res[2], channeldata
