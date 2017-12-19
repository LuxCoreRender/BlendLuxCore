import bpy
from bpy.props import EnumProperty, BoolProperty


TILED_DESCRIPTION = (
    "Render the image in quadratic chunks instead of sampling the whole film at once;\n"
    "Causes lower memory usage; Uses a special sampler"
)

SIMPLE_DESC = "Recommended for scenes with simple lighting (outdoors, studio setups, indoors with large windows)"
COMPLEX_DESC = "Recommended for scenes with difficult lighting (caustics, indoors with small windows)"


class LuxCoreConfig(bpy.types.PropertyGroup):
    # engines = [
    #     ("PATHCPU", "Path CPU", "Path tracer", 0),
    #     ("TILEPATHCPU", "Tile Path CPU", "Path tracer rendering in tiles", 1),
    #     ("BIDIRCPU", "Bidir CPU", "Bidirectional path tracer", 2),
    #     ("PATHOCL", "Path OpenCL", "OpenCL version of Path CPU", 3),
    #     ("TILEPATHOCL", "Tile Path OpenCL", "OpenCL version of Tile Path CPU", 4),
    # ]
    # engine = EnumProperty(name="Engine", items=engines, default="PATHCPU")

    engines = [
        ("PATH", "Path", "Unidirectional path tracer; " + SIMPLE_DESC, 0),
        ("BIDIR", "Bidir", "Bidirectional path tracer; " + COMPLEX_DESC, 1),
    ]
    engine = EnumProperty(name="Engine", items=engines, default="PATH")

    # Only available when tiled rendering is off
    samplers = [
        ("SOBOL", "Sobol", SIMPLE_DESC, 0),
        ("METROPOLIS", "Metropolis", COMPLEX_DESC, 1),
    ]
    sampler = EnumProperty(name="Sampler", items=samplers, default="SOBOL")
    # A trick so we can show the user that bidir should only be used with Metropolis
    bidir_sampler = EnumProperty(name="Sampler", items=samplers, default="METROPOLIS",
                                 description="Only Metropolis makes sense for Bidir")

    # Only available when engine is PATH (not BIDIR)
    devices = [
        ("CPU", "CPU", "Use the arithmetic logic units in your central processing unit", 0),
        ("OCL", "OpenCL", "Use the good ol' pixel cruncher", 1),
    ]
    device = EnumProperty(name="Device", items=devices, default="CPU")
    # A trick so we can show the user that bidir can only be used on the CPU (see UI code)
    bidir_device = EnumProperty(name="Device", items=devices, default="CPU", description="Bidir only available on CPU")

    tiled = BoolProperty(name="Tiled", default=False, description=TILED_DESCRIPTION)


