import bpy
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatProperty, PointerProperty


TILED_DESCRIPTION = (
    "Render the image in quadratic chunks instead of sampling the whole film at once;\n"
    "Causes lower memory usage; Uses a special sampler"
)

SIMPLE_DESC = "Recommended for scenes with simple lighting (outdoors, studio setups, indoors with large windows)"
COMPLEX_DESC = "Recommended for scenes with difficult lighting (caustics, indoors with small windows)"

FILTER_DESC = (
    "Pixel filtering slightly blurs the image, which reduces noise and \n"
    "fireflies and leads to a more realistic image impression;\n"
    "When using OpenCL, disabling this option can increase rendering speed"
)
FILTER_WIDTH_DESC = "Filter width in pixels; lower values result in a sharper image, higher values smooth out noise"


class LuxCoreConfigPath(PropertyGroup):
    """
    path.*
    Stored in LuxCoreConfig, accesss with scene.luxcore.config.path
    """
    # TODO: helpful descriptions
    # path.pathdepth.total
    depth_total = IntProperty(name="Total Path Depth", default=6, min=1, soft_max=16)
    # path.pathdepth.diffuse
    depth_diffuse = IntProperty(name="Diffuse", default=4, min=1, soft_max=16)
    # path.pathdepth.glossy
    depth_glossy = IntProperty(name="Glossy", default=4, min=1, soft_max=16)
    # path.pathdepth.specular
    depth_specular = IntProperty(name="Specular", default=6, min=1, soft_max=16)

    # TODO: can we estimate a good clamp value automatically?
    # TODO: if not, add a warning/info label
    use_clamping = BoolProperty(name="Clamp Output", default=False)
    # path.clamping.variance.maxvalue
    clamping = FloatProperty(name="Max Brightness", default=1000, min=0)

    # TODO This will be set automatically on export when transparent film is used
    # path.forceblackbackground.enable

    # We probably don't need to expose these properties because they have good
    # default values that should very rarely (or never?) need adjustment
    # path.russianroulette.depth
    # path.russianroulette.cap


class LuxCoreConfigTile(PropertyGroup):
    """
    tile.*
    Stored in LuxCoreConfig, accesss with scene.luxcore.config.tile
    """
    # tilepath.sampling.aa.size
    path_sampling_aa_size = IntProperty(name="AA Samples", default=3, min=1, soft_max=13)
    # tile.size
    size = IntProperty(name="Tile Size", default=64, min=16, soft_min=32, soft_max=256)
    # tile.multipass.enable
    multipass_enable = BoolProperty(name="Multipass", default=True)
    # TODO: min/max correct?
    # tile.multipass.convergencetest.threshold
    multipass_convtest_threshold = FloatProperty(name="Convergence Threshold", default=(6 / 256),
                                                 min=0.0000001, soft_max=(6 / 256))
    # TODO min/max/default
    # tile.multipass.convergencetest.threshold.reduction
    multipass_convtest_threshold_reduction = FloatProperty(name="Threshold Reduction", default=0.5, min=0.001,
                                                           soft_min=0.1, max=0.99, soft_max=0.9)
    # TODO do we need to expose this? In LuxBlend we didn't
    # tile.multipass.convergencetest.warmup.count
    # multipass_convtest_warmup = IntProperty(name="Convergence Warmup", default=32, min=0, soft_max=128)


class LuxCoreConfigOpenCL(PropertyGroup):
    """
    opencl.*
    Stored in LuxCoreConfig, accesss with scene.luxcore.config.opencl
    """
    # TODO: opencl.platform.index - do we expose this?
    # opencl.cpu.use
    use_cpu = BoolProperty(name="Use CPUs", default=False)
    # opencl.gpu.use
    use_gpu = BoolProperty(name="Use GPUs", default=True)

    # TODO This will be set automatically on export when custom device selection is enabled
    # opencl.devices.select

    # We probably don't need to expose these properties
    # opencl.cpu.workgroup.size
    # opencl.gpu.workgroup.size


class LuxCoreConfig(PropertyGroup):
    """
    Main config storage class.
    Access (in ui or export) with scene.luxcore.config
    """

    # These settings are mostly not directly transferrable to LuxCore properties
    # They need some if/else decisions and aggregation, e.g. to build the engine name from parts
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
    bidir_device = EnumProperty(name="Device", items=devices, default="CPU",
                                description="Bidir only available on CPU")

    use_tiles = BoolProperty(name="Tiled", default=False, description=TILED_DESCRIPTION)

    # Special properties of the various engines
    path = PointerProperty(type=LuxCoreConfigPath)
    tile = PointerProperty(type=LuxCoreConfigTile)
    opencl = PointerProperty(type=LuxCoreConfigOpenCL)
    # BIDIR properties
    # light.maxdepth
    bidir_light_maxdepth = IntProperty(name="Light Depth", default=10, min=1, soft_max=16)
    # path.maxdepth
    bidir_path_maxdepth = IntProperty(name="Eye Depth", default=10, min=1, soft_max=16)

    # Pixel filter
    use_filter = BoolProperty(name="Use Pixel Filter", default=True, description=FILTER_DESC)
    filter_width = FloatProperty(name="Width", default=1.5, min=0.5, soft_max=3, description=FILTER_WIDTH_DESC)

    # FILESAVER options
    use_filesaver = BoolProperty(name="Only write LuxCore scene", default=False)
    filesaver_format_items = [
        ("TXT", "Text", "Save as .scn and .cfg text files", 0),
        ("BIN", "Binary", "Save as .bcf binary file", 1),
    ]
    filesaver_format = EnumProperty(name="", items=filesaver_format_items, default="BIN")
