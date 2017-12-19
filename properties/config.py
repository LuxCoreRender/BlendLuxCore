import bpy
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatProperty, PointerProperty


TILED_DESCRIPTION = (
    "Render the image in quadratic chunks instead of sampling the whole film at once;\n"
    "Causes lower memory usage; Uses a special sampler"
)

SIMPLE_DESC = "Recommended for scenes with simple lighting (outdoors, studio setups, indoors with large windows)"
COMPLEX_DESC = "Recommended for scenes with difficult lighting (caustics, indoors with small windows)"


class LuxCoreConfig(PropertyGroup):
    # TODO: thread count (maybe use the controls from Blender, like Cycles does?)

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

    # Special properties of the various engines
    path = PointerProperty(type=LuxCoreConfigPath)
    tile = PointerProperty(type=LuxCoreConfigTile)
    opencl = PointerProperty(type=LuxCoreConfigOpenCL)
    # I'm not creating a class for only one property
    light_maxdepth = IntProperty(name="Light Depth", default=5, min=1, soft_max=16)


class LuxCoreConfigPath(PropertyGroup):
    """ path.* """
    # TODO: helpful descriptions
    depth_total = IntProperty(name="Path Depth", default=6, min=1, soft_max=16)
    depth_diffuse = IntProperty(name="Diffuse Depth", default=4, min=1, soft_max=16)
    depth_glossy = IntProperty(name="Glossy Depth", default=4, min=1, soft_max=16)
    depth_specular = IntProperty(name="Specular Depth", default=6, min=1, soft_max=16)

    # TODO: can we estimate a good clamp value automatically?
    # TODO: if not, add a warning/info label
    use_clamping = BoolProperty(name="Clamp Output", default=False)
    clamping = FloatProperty(name="Max Brightness", default=0, min=0)

    # This will be set automatically on export when transparent film is used
    # path.forceblackbackground.enable

    # We probably don't need to expose these properties
    # path.russianroulette.depth
    # path.russianroulette.cap


class LuxCoreConfigTile(PropertyGroup):
    """ tile.* """
    path_sampling_aa_size = IntProperty(name="AA Samples", default=3, min=1, soft_max=13)
    size = IntProperty(name="Tile Size", default=32, min=8, soft_max=256)
    multipass_enable = BoolProperty(name="Multipass", default=True)
    # TODO: min/max correct?
    multipass_convtest_threshold = FloatProperty(name="Convergence Threshold", default=(6 / 256),
                                                 min=0.0000001, soft_max=(6 / 256))
    # TODO min/max/default
    multipass_convtest_threshold_reduction = FloatProperty(name="Threshold Reduction")
    multipass_convtest_warmup = IntProperty(name="Convergence Warmup", default=32, min=0, soft_max=128)


class LuxCoreConfigOpenCL(PropertyGroup):
    """ opencl.* """
    # TODO: opencl.platform.index - do we expose this?
    use_cpu = BoolProperty(name="Use CPUs", default=False)
    use_gpu = BoolProperty(name="Use GPUs", default=True)

    # This will be set automatically on export when custom device selection is enabled
    # opencl.devices.select

    # We probably don't need to expose these properties
    # opencl.cpu.workgroup.size
    # opencl.gpu.workgroup.size
