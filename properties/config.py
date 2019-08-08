import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    EnumProperty, BoolProperty, IntProperty, FloatProperty,
    PointerProperty, StringProperty,
)
from math import radians
from .halt import NOISE_THRESH_WARMUP_DESC, NOISE_THRESH_STEP_DESC


TILED_DESCRIPTION = (
    "Render the image in quadratic chunks instead of sampling the whole film at once;\n"
    "Causes lower memory usage; Uses a special sampler"
)
TILE_SIZE_DESC = (
    "Note that OpenCL devices will automatically render multiple tiles if it increases performance"
)

AA_SAMPLE_DESC = (
    "How many AA samples to compute per pass. Higher values increase memory usage, but lead to better performance. "
    "Note that this number is squared, so e.g. a value of 5 will lead to 25 samples per pixel after one pass"
)

THRESH_REDUCT_DESC = (
    "Multiply noise level with this value after all tiles have converged, "
    "then continue with the lowered noise level"
)
THRESH_WARMUP_DESC = "How many samples to render before starting the convergence tests"

SIMPLE_DESC = "Recommended for scenes with simple lighting (outdoors, studio setups, indoors with large windows)"
COMPLEX_DESC = "Recommended for scenes with difficult lighting (caustics, indoors with small windows)"

FILTER_DESC = (
    "Pixel filtering slightly blurs the image, which reduces noise and \n"
    "fireflies and leads to a more realistic image impression;\n"
    "When using OpenCL, disabling this option can increase rendering speed"
)
FILTER_WIDTH_DESC = "Filter width in pixels; lower values result in a sharper image, higher values smooth out noise"

CLAMPING_DESC = (
    "Use to reduce fireflies. The optimal clamping value is computed after "
    "rendering for 10 seconds, but only if clamping is DISABLED"
)

SEED_DESC = (
    "Seed for random number generation. Images rendered with "
    "the same seed will have the same noise pattern"
)
ANIM_SEED_DESC = "Use different seed values for different frames"

SOBOL_ADAPTIVE_STRENGTH_DESC = (
    "A value of 0 means that each pixel is sampled equally, higher values "
    "focus more samples on noisy areas of the image"
)

LOG_POWER_DESC = (
    "(Default) Sample lights according to their brightness, but weighting very bright "
    "lights not much more than dim lights (recommended when using environment "
    "lights (HDRI/sky) plus few small light sources)"
)

POWER_DESC = (
    "Sample lights according to their brightness (recommended when using very bright "
    "lights (e.g. sun) together with highpoly meshlights with more than about 10 tris)"
)

UNIFORM_DESC = "Sample all lights equally, not according to their brightness"

DLSC_DESC = (
    "Use the DLSC in scenes with many light sources if each of them only "
    "lights up a small part of the scene (example: a city at night). "
    "The DLSC is built before the rendering starts"
)

LARGE_STEP_RATE_DESC = (
    "Probability of generating a large sample mutation. "
    "Low values cause the sampler to focus more on "
    "caustics and other hotspots it found, while high "
    "values make the sampler behave more like a pure "
    "random sampler"
)

MAX_CONSECUTIVE_REJECT_DESC = (
    "Number of consecutive rejects before a next "
    "mutation is forced. Low values can cause bias"
)

IMAGE_MUTATION_RATE_DESC = "Maximum distance over the image plane for a small mutation"

LOOKUP_RADIUS_DESC = (
    "Choose this value according to the size of your scene. "
    "The default value is suited for a room-sized scene. "
    "Larger values can degrade rendering performance"
)

LOOKUP_MAXCOUNT_DESC = (
    "How many photons to consider at most per lookup. Larger values can give "
    "more accurate results, but may slow down rendering"
)

NORMAL_ANGLE_DESC = (
    "Only if the angle between two faces is smaller than this value, "
    "cache entries can be shared by the surfaces"
)

PHOTONGI_HALTTHRESH_DESC = (
    "Max. convergence error. Photons are traced until the convergence error is below "
    "this threshold or the photon count is reached. Lower values lead to higher quality "
    "cache, but take longer to compute"
)

HYBRID_BACKFORWARD_DESC = (
    "Trace rays from lights in addition to rays from the camera. Enable if your scene contains caustics"
)
HYBRID_BACKFORWARD_LIGHTPART_DESC = (
    "Controls the amount of computed light rays. Higher values assign more computational power "
    "to caustic rendering. Using 0% disables light tracing, using 100% disables camera rays completely"
)
HYBRID_BACKFORWARD_GLOSSINESS_DESC = (
    "If a material's roughness is lower than this threshold, it is sampled from lights, "
    "otherwise it is sampled from the camera (normal path tracing)"
)

# Used in enum callback
film_opencl_device_items = []


class LuxCoreConfigPath(PropertyGroup):
    """
    path.*
    Stored in LuxCoreConfig, accesss with scene.luxcore.config.path
    """
    # TODO: helpful descriptions
    # path.pathdepth.total
    depth_total: IntProperty(name="Total Path Depth", default=6, min=1, soft_max=16)
    # path.pathdepth.diffuse
    depth_diffuse: IntProperty(name="Diffuse", default=4, min=1, soft_max=16)
    # path.pathdepth.glossy
    depth_glossy: IntProperty(name="Glossy", default=4, min=1, soft_max=16)
    # path.pathdepth.specular
    depth_specular: IntProperty(name="Specular", default=6, min=1, soft_max=16)

    hybridbackforward_enable: BoolProperty(name="Add Light Tracing", default=False,
                                           description=HYBRID_BACKFORWARD_DESC)
    hybridbackforward_lightpartition: FloatProperty(name="Light Rays", default=20, min=0, max=100,
                                                    subtype="PERCENTAGE",
                                                    description=HYBRID_BACKFORWARD_LIGHTPART_DESC)
    hybridbackforward_glossinessthresh: FloatProperty(name="Glossiness Threshold", default=0.049, min=0, max=1,
                                                      description=HYBRID_BACKFORWARD_GLOSSINESS_DESC)

    use_clamping: BoolProperty(name="Clamp Output", default=False, description=CLAMPING_DESC)
    # path.clamping.variance.maxvalue
    clamping: FloatProperty(name="Max Brightness", default=1000, min=0, description=CLAMPING_DESC)
    # This should only be set in the engine code after export. Only show a read-only label to the user.
    suggested_clamping_value: FloatProperty(name="", default=-1)

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
    path_sampling_aa_size: IntProperty(name="AA Samples", default=3, min=1, soft_max=13,
                                        description=AA_SAMPLE_DESC)

    # tile.size
    size: IntProperty(name="Tile Size", default=64, min=16, soft_min=32, soft_max=256, subtype="PIXEL",
                       description=TILE_SIZE_DESC)

    # tile.multipass.enable
    multipass_enable: BoolProperty(name="Multipass", default=True, description="")

    # TODO: unify with halt condition noise threshold settings

    # tile.multipass.convergencetest.threshold
    multipass_convtest_threshold: FloatProperty(name="Convergence Threshold", default=(6 / 256),
                                                 min=0.0000001, soft_max=(6 / 256),
                                                 description="")
    # tile.multipass.convergencetest.threshold.reduction
    multipass_convtest_threshold_reduction: FloatProperty(name="Threshold Reduction", default=0.5, min=0.001,
                                                           soft_min=0.1, max=0.99, soft_max=0.9,
                                                           description=THRESH_REDUCT_DESC)
    # tile.multipass.convergencetest.warmup.count
    multipass_convtest_warmup: IntProperty(name="Convergence Warmup", default=32, min=0,
                                            soft_min=8, soft_max=128,
                                            description=THRESH_WARMUP_DESC)


class LuxCoreConfigDLSCache(PropertyGroup):
    show_advanced: BoolProperty(name="Show Advanced", default=False)

    entry_radius_auto: BoolProperty(name="Automatic Entry Radius", default=True,
                                     description="Automatically choose a good entry radius")
    entry_radius: FloatProperty(name="Entry Radius", default=0.15, min=0, subtype="DISTANCE",
                                 description="Choose this value according to the size of your scene. "
                                             "The default (15 cm) is suited for a room-sized scene")
    entry_normalangle: FloatProperty(name="Normal Angle",
                                      default=radians(10), min=0, max=radians(90), subtype="ANGLE")
    entry_maxpasses: IntProperty(name="Max. Passes", default=1024, min=0)
    entry_convergencethreshold: FloatProperty(name="Convergence Threshold",
                                               default=1, min=0, max=100, subtype="PERCENTAGE")
    entry_warmupsamples: IntProperty(name="Warmup Samples", default=12, min=0,
                                      description="Increase this value if splotchy artifacts appear in the image")
    entry_volumes_enable: BoolProperty(name="Place Entries in Volumes", default=False,
                                        description="Enable/disable placement of entries in volumes (in mid-air)")

    lightthreshold: FloatProperty(name="Light Threshold", default=1, min=0, max=100, subtype="PERCENTAGE")
    targetcachehitratio: FloatProperty(name="Target Cache Hit Ratio",
                                        default=99.5, min=0, max=100, subtype="PERCENTAGE")
    maxdepth: IntProperty(name="Max. Depth", default=4, min=0)
    maxsamplescount: IntProperty(name="Max. Samples", default=10000000, min=0)


class LuxCoreConfigPhotonGI(PropertyGroup):
    enabled: BoolProperty(name="Enabled", default=False)

    # Shared settings
    photon_maxcount: FloatProperty(name="Photon Count (Millions)", default=20, min=1, soft_max=100,
                                    precision=0, step=10,
                                    description="Max. number of photons traced (value in millions)")
    photon_maxdepth: IntProperty(name="Photon Depth", default=8, min=3, max=64,
                                  description="Max. depth of photon paths. At each bounce, a photon might be stored")
    # Indirect cache
    indirect_enabled: BoolProperty(name="Indirect Cache", default=True)
    indirect_haltthreshold_preset_items = [
        ("final", "Final Render", "Halt Threshold 5%", 0),
        ("preview", "Preview", "Halt Threshold 15%", 1),
        ("custom", "Custom", "", 2),
    ]
    indirect_haltthreshold_preset: EnumProperty(name="Quality", items=indirect_haltthreshold_preset_items,
                                                 default="final",
                                                 description=PHOTONGI_HALTTHRESH_DESC)
    indirect_haltthreshold_custom: FloatProperty(name="Halt Threshold", default=5, min=0.001, max=100,
                                                  precision=0, subtype="PERCENTAGE",
                                                  description=PHOTONGI_HALTTHRESH_DESC)
    indirect_lookup_radius_auto: BoolProperty(name="Automatic Lookup Radius", default=True,
                                               description="Automatically choose a good lookup radius")
    indirect_lookup_radius: FloatProperty(name="Lookup Radius", default=0.15, min=0.00001, subtype="DISTANCE",
                                           description=LOOKUP_RADIUS_DESC)
    indirect_normalangle: FloatProperty(name="Normal Angle", default=radians(10), min=0, max=radians(90),
                                         subtype="ANGLE", description=NORMAL_ANGLE_DESC)
    # I use 0.049 as default because then glossy materials with default roughness (0.05) are cached
    indirect_glossinessusagethreshold: FloatProperty(name="Glossiness Threshold", default=0.049, min=0, max=1,
                                                      description="Only if a material's roughness is higher than "
                                                                  "this threshold, cache entries are stored on it")
    indirect_usagethresholdscale: FloatProperty(name="Brute Force Radius Scale", default=8, min=0, precision=1,
                                                 description="In corners and other areas with fine detail, LuxCore "
                                                             "uses brute force pathtracing instead of the cache "
                                                             "entries. This parameter is multiplied with the lookup "
                                                             "radius and controls the size of the pathtraced area "
                                                             "around corners. "
                                                             "Smaller values can increase performance, but might lead "
                                                             "to splotches and light leaks near corners. Use a larger "
                                                             "value if you encounter such artifacts")

    # Caustic cache
    caustic_enabled: BoolProperty(name="Caustic Cache", default=False)
    caustic_maxsize: FloatProperty(name="Max. Size (Millions)", default=1, soft_min=0.1, min=0.01, soft_max=10,
                                    precision=0, step=1,
                                    description="Max. number of photons stored in caustic cache (value in millions)")
    caustic_lookup_radius: FloatProperty(name="Lookup Radius", default=0.075, min=0.00001, subtype="DISTANCE",
                                          description=LOOKUP_RADIUS_DESC)
    caustic_lookup_maxcount: IntProperty(name="Lookup Max. Count", default=128, min=1,
                                          description=LOOKUP_MAXCOUNT_DESC)
    caustic_normalangle: FloatProperty(name="Normal Angle", default=radians(10), min=0, max=radians(90),
                                        subtype="ANGLE", description=NORMAL_ANGLE_DESC)
    caustic_merge_enabled: BoolProperty(name="Merge Caustic Photons", default=True,
                                         description="Merge clumped up photons. Improves rendering speed, "
                                                     "but leads to blurring if the radius is too large")
    caustic_merge_radius_scale: FloatProperty(name="Radius Scale", default=0.25, min=0, max=0.4, step=0.1,
                                               description="Scale factor for the merge radius, multiplied with lookup "
                                                           "radius. Smaller values lead to sharper caustics, but worse "
                                                           "rendering performance. Larger values lead to blurred "
                                                           "caustics, but faster rendering")

    debug_items = [
        ("off", "Off (Final Render Mode)", "", 0),
        ("showindirect", "Show Indirect", "View the indirect light cache", 1),
        ("showindirectpathmix", "Show Indirect/Path Mix",
         "Blue = cache is used, red = brute force path tracing is used", 3),
        ("showcaustic", "Show Caustic", "View the caustic cache", 2),
    ]
    debug: EnumProperty(name="Debug", items=debug_items, default="off",
                         description="Choose between final render mode or a debug representation of the caches")

    file_path: StringProperty(name="File Path", subtype="FILE_PATH",
                               description="File path to the PhotonGI cache file")
    save_or_overwrite: BoolProperty(name="", default=False,
                                     description="Save the cache to a file or overwrite the existing cache file. "
                                                 "If you want to use the saved cache, disable this option")


class LuxCoreConfigEnvLightCache(PropertyGroup):
    enabled: BoolProperty(name="Enabled", default=False,
                          description="Compute a cache with multiple visibility maps for the scene (works like "
                                      "automatic portals). Note that it might consume a lot of RAM")
    # TODO descriptions
    map_width: IntProperty(name="Map Width", default=256, min=16, soft_max=256)
    samples: IntProperty(name="Samples", default=1, min=1, soft_max=32)


class LuxCoreConfigNoiseEstimation(PropertyGroup):
    warmup: IntProperty(name="Warmup Samples", default=8, min=1,
                         description=NOISE_THRESH_WARMUP_DESC)
    step: IntProperty(name="Test Step Samples", default=32, min=1, soft_min=16,
                       description=NOISE_THRESH_STEP_DESC)


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
    engine: EnumProperty(name="Engine", items=engines, default="PATH")

    # Only available when tiled rendering is off
    samplers = [
        ("SOBOL", "Sobol", SIMPLE_DESC, 0),
        ("METROPOLIS", "Metropolis", COMPLEX_DESC, 1),
        ("RANDOM", "Random", "Recommended only if the BCD denoiser is used (use Sobol otherwise)", 2),
    ]
    sampler: EnumProperty(name="Sampler", items=samplers, default="SOBOL")

    # SOBOL properties
    sobol_adaptive_strength: FloatProperty(name="Adaptive Strength", default=0.95, min=0, max=0.95,
                                            description=SOBOL_ADAPTIVE_STRENGTH_DESC)

    # Noise estimation (used by adaptive samplers like SOBOL and RANDOM)
    noise_estimation: PointerProperty(type=LuxCoreConfigNoiseEstimation)

    # METROPOLIS properties
    # sampler.metropolis.largesteprate
    metropolis_largesteprate: FloatProperty(name="Large Mutation Probability", default=40,
                                             min=0, max=100, precision=0, subtype="PERCENTAGE",
                                             description=LARGE_STEP_RATE_DESC)
    # sampler.metropolis.maxconsecutivereject
    metropolis_maxconsecutivereject: IntProperty(name="Max Consecutive Rejects", default=512, min=0,
                                                  description=MAX_CONSECUTIVE_REJECT_DESC)
    # sampler.metropolis.imagemutationrate
    metropolis_imagemutationrate: FloatProperty(name="Image Mutation Rate", default=10,
                                                 min=0, max=100, precision=0, subtype="PERCENTAGE",
                                                 description=IMAGE_MUTATION_RATE_DESC)

    # Only available when engine is PATH (not BIDIR)
    devices = [
        ("CPU", "CPU", "Use the arithmetic logic units in your central processing unit", 0),
        ("OCL", "OpenCL", "Use the good ol' pixel cruncher", 1),
    ]
    device: EnumProperty(name="Device", items=devices, default="CPU")
    # A trick so we can show the user that bidir can only be used on the CPU (see UI code)
    bidir_device: EnumProperty(name="Device", items=devices, default="CPU",
                                description="Bidir only available on CPU")

    use_tiles: BoolProperty(name="Tiled", default=False, description=TILED_DESCRIPTION)

    # Special properties of the various engines
    path: PointerProperty(type=LuxCoreConfigPath)
    tile: PointerProperty(type=LuxCoreConfigTile)
    # BIDIR properties
    # light.maxdepth
    # TODO description
    bidir_light_maxdepth: IntProperty(name="Light Depth", default=10, min=1, soft_max=16)
    # path.maxdepth
    # TODO description
    bidir_path_maxdepth: IntProperty(name="Eye Depth", default=10, min=1, soft_max=16)

    # Pixel filter
    filters = [
        ("BLACKMANHARRIS", "Blackman-Harris", "Default, usually the best option", 0),
        ("MITCHELL_SS", "Mitchell", "Sharp, but can produce black ringing artifacts around bright pixels", 1),
        ("GAUSSIAN", "Gaussian", "Blurry", 2),
        ("NONE", "None", "Disable pixel filtering. Fastest setting when rendering on GPU", 3)
    ]
    filter: EnumProperty(name="Filter", items=filters, default="BLACKMANHARRIS",
                          description=FILTER_DESC)
    filter_width: FloatProperty(name="Filter Width", default=1.5, min=0.5, soft_max=3,
                                 description=FILTER_WIDTH_DESC, subtype="PIXEL")
    gaussian_alpha: FloatProperty(name="Gaussian Filter Alpha", default=2, min=0.1, max=10,
                                   description="Gaussian rate of falloff. Lower values give blurrier images")

    # Light strategy
    light_strategy_items = [
        ("LOG_POWER", "Log Power", LOG_POWER_DESC, 0),
        ("POWER", "Power", POWER_DESC, 1),
        ("UNIFORM", "Uniform", UNIFORM_DESC, 2),
        ("DLS_CACHE", "Direct Light Sampling Cache", DLSC_DESC, 3),
    ]
    light_strategy: EnumProperty(name="Light Strategy", items=light_strategy_items, default="LOG_POWER",
                                  description="Decides how the lights in the scene are sampled")

    # Special properties of the direct light sampling cache
    dls_cache: PointerProperty(type=LuxCoreConfigDLSCache)
    # Special properties of the photon GI cache
    photongi: PointerProperty(type=LuxCoreConfigPhotonGI)
    # Special properties of the env. light cache (aka automatic portals)
    envlight_cache: PointerProperty(type=LuxCoreConfigEnvLightCache)

    # FILESAVER options
    use_filesaver: BoolProperty(name="Only write LuxCore scene", default=False)
    filesaver_format_items = [
        ("TXT", "Text", "Save as .scn and .cfg text files", 0),
        ("BIN", "Binary", "Save as .bcf binary file", 1),
    ]
    filesaver_format: EnumProperty(name="", items=filesaver_format_items, default="TXT")
    filesaver_path: StringProperty(name="", subtype="DIR_PATH")

    # Seed
    seed: IntProperty(name="Seed", default=0, min=0, description=SEED_DESC)
    use_animated_seed: BoolProperty(name="Animated Seed", default=False, description=ANIM_SEED_DESC)

    # Min. epsilon settings (drawn in ui/units.py)
    show_min_epsilon: BoolProperty(name="Advanced LuxCore Settings", default=False,
                                    description="Show/Hide advanced LuxCore features. "
                                                "Only change them if you know what you are doing")
    min_epsilon: FloatProperty(name="Min. Epsilon", default=1e-5, soft_min=1e-6, soft_max=1e-1,
                                precision=5,
                                description="User higher values when artifacts due to floating point precision "
                                            "issues appear in the rendered image")
    max_epsilon: FloatProperty(name="Max. Epsilon", default=1e-1, soft_min=1e-3, soft_max=1e+2,
                                precision=5,
                                description="Might need adjustment along with the min epsilon to avoid "
                                            "artifacts due to floating point precision issues")

    film_opencl_enable: BoolProperty(name="Use OpenCL", default=True,
                                      description="Use OpenCL to accelerate tonemapping and other imagepipeline "
                                                  "operations (applies to viewport and final render). "
                                                  "Disabling this option will save a bit of RAM, especially if "
                                                  "the render resolution is large. "
                                                  "This option is ignored in Non-OpenCL builds")

    def film_opencl_device_items_callback(self, context):
        devices = context.scene.luxcore.opencl.devices
        items = [("none", "None", "", 0)]
        items += [(str(i), device.name, "", i + 1) for i, device in enumerate(devices) if device.type == "OPENCL_GPU"]
        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        global film_opencl_device_items
        film_opencl_device_items = items
        return items

    film_opencl_device: EnumProperty(name="Device", items=film_opencl_device_items_callback,
                                      description="Which device to use to compute the imagepipeline")
