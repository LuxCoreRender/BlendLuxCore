from bpy.types import PropertyGroup
from bpy.props import (
    EnumProperty, BoolProperty, IntProperty, FloatProperty,
    PointerProperty, StringProperty,
)
from math import radians
from .halt import NOISE_THRESH_WARMUP_DESC, NOISE_THRESH_STEP_DESC
from .. import utils


PATH_DESC = (
    'Traces rays from the camera (and from lights, if "Add Light Tracing" or caustics cache are used).\n'
    'Suited for almost all scene types and lighting scenarios.\n'
    'Can run on the CPU, GPU or both.\n'
    'Supports several caches to accelerate indirect light, environment light sampling and many-light sampling.\n'
    'Can render complex SDS-caustics (e.g. caustics seen in a mirror) efficiently with the caustics cache.\n'
    'All AOV types and special features like shadow catcher or indirect light visibility flags for lights are supported'
)

BIDIR_DESC = (
    "Traces and combines rays from the camera and lights.\n"
    "Suited for some special edge-case types of scenes that can't be rendered efficiently by the Pathtracing engine.\n"
    "Slower than the Path engine otherwise.\n"
    'Limited to the CPU, can not run on the GPU.\n'
    "Can not render complex SDS-caustics (e.g. caustics seen in a mirror) efficiently.\n"
    "Does not support all AOV types and special features like shadow catcher or indirect light visibility flags for lights"
)

SOBOL_DESC = "Optimized random noise pattern. Supports noise-aware adaptive sampling"
METROPOLIS_DESC = "Sampler that focuses samples on brighter parts of the image. Not noise-aware. Suited for rendering caustics"
RANDOM_DESC = (
    "Random noise pattern. Supports noise-aware adaptive sampling."
    "Recommended only if the BCD denoiser is used (use Sobol otherwise)"
)

TILED_DESCRIPTION = (
    'Use the special "Tiled Path" engine, which is slower than the regular Path engine, but uses less memory. '
    'Does not support the "Add Light Tracing" option'
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

FILTER_DESC = (
    "Pixel filtering blends pixels with their neighbours according to the chosen filter type. "
    "This can be used to blur or sharpen the image. Note that it is recommended to disable "
    "pixel filtering when denoising is used"
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
    "lights up a small part of the scene (example: a city at night). \n"
    "Only used during final render"
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
    "Controls the sharpness of the caustics. "
    "Choose this value according to the size of your scene and the required detail in your caustics. "
    "Too large values can degrade rendering performance, too small values can lead to non-resolving, noisy caustics"
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

PHOTONGI_GLOSSINESSTHRESH_DESC = (
    "If a material's roughness is higher than this threshold, indirect cache entries can be stored on it. "
    "If the roughness is below the threshold, it will be considered in the caustic cache computation"
)

PHOTONGI_INDIRECT_USAGETHRESHOLDSCALE_DESC = (
    "In corners and other areas with fine detail, LuxCore uses brute force pathtracing instead of the cache "
    "entries. This parameter is multiplied with the lookup radius and controls the size of the pathtraced area "
    "around corners. Smaller values can increase performance, but might lead to splotches and light leaks near "
    "corners. Use a larger value if you encounter such artifacts"
)

HYBRID_BACKFORWARD_DESC = (
    "Trace rays from lights in addition to rays from the camera. Enable if your scene contains caustics"
)
HYBRID_BACKFORWARD_LIGHTPART_DESC = (
    "Controls the amount of computed light rays. Higher values assign more computational power "
    "to caustic rendering. Using 0% disables light tracing, using 100% disables camera rays completely"
)
HYBRID_BACKFORWARD_LIGHTPART_OPENCL_DESC = (
    "Controls the amount of light rays computed on the CPU (the GPU can only compute camera rays). "
    "Using 0% disables light tracing, using 100% means that the CPU only performs light tracing"
)
HYBRID_BACKFORWARD_GLOSSINESS_DESC = (
    "If a material's roughness is lower than this threshold, it is sampled from lights, "
    "otherwise it is sampled from the camera (normal path tracing)"
)

ENVLIGHT_CACHE_DESC = (
    "Enable in scenes where the world environment is only visible through small openings (e.g. a room with small windows). "
    "Do not use in open scenes, as it can be detrimental to performance in this case. "
    "Computes a cache with multiple visibility maps (works like "
    "automatic portals). Note that it might consume a lot of RAM. \n"
    "Only used during final render"
)

MIPMAPMEM_DESC = (
    "For each image texture, a .tx mipmap cache with multiple sizes (e.g. 256x256, 128x128, 64x64 etc.) is created. "
    "When rendering, the smallest possible mipmap resolution is picked automatically. This resize policy saves less "
    "memory than the \"auto-scale to lowest size\" policy, but needs almost no preprocessing time after the first render"
)
MINMEM_DESC = (
    "Before the rendering starts, LuxCore checks how large each image texture is visible on the film. If the image "
    "is larger than needed, for example because it is only seen from far away, the image is scaled down. This policy "
    "saves as much memory as possible without affecting render quality, but needs some preprocessing time for every render"
)
FIXED_DESC = (
    "All images are scaled the same amount (set with the Scale parameter)"
)


class LuxCoreConfigPath(PropertyGroup):
    """
    path.*
    Stored in LuxCoreConfig, accesss with scene.luxcore.config.path
    """
    # TODO: helpful descriptions
    # path.pathdepth.total
    depth_total: IntProperty(name="Total Path Depth", default=12, min=1, soft_max=128)
    # path.pathdepth.diffuse
    depth_diffuse: IntProperty(name="Diffuse", default=4, min=1, soft_max=128)
    # path.pathdepth.glossy
    depth_glossy: IntProperty(name="Glossy", default=4, min=1, soft_max=128)
    # path.pathdepth.specular
    depth_specular: IntProperty(name="Specular", default=12, min=1, soft_max=128)

    hybridbackforward_enable: BoolProperty(name="Add Light Tracing", default=False,
                                           description=HYBRID_BACKFORWARD_DESC)
    hybridbackforward_lightpartition: FloatProperty(name="Light Rays", default=20, min=0, max=100,
                                                    subtype="PERCENTAGE",
                                                    description=HYBRID_BACKFORWARD_LIGHTPART_DESC)
    # Separate property so we can use a different default that makes more sense for OpenCL
    hybridbackforward_lightpartition_opencl: FloatProperty(name="Light Rays", default=100, min=0, max=100,
                                                    subtype="PERCENTAGE",
                                                    description=HYBRID_BACKFORWARD_LIGHTPART_OPENCL_DESC)
    hybridbackforward_glossinessthresh: FloatProperty(name="Glossiness Threshold", default=0.049, min=0, max=1,
                                                      description=HYBRID_BACKFORWARD_GLOSSINESS_DESC)

    use_clamping: BoolProperty(name="Clamp Output", default=False, description=CLAMPING_DESC)
    # path.clamping.variance.maxvalue
    clamping: FloatProperty(name="Max Brightness", default=10, min=0,soft_max=10000,  description=CLAMPING_DESC)
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
    # Overrides other light strategies when enabled
    enabled: BoolProperty(name="", default=False, description=DLSC_DESC)

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

    file_path: StringProperty(name="File Path", subtype="FILE_PATH",
                              description="File path to the DLS cache file")
    save_or_overwrite: BoolProperty(name="", default=False,
                                    description="Save the cache to a file or overwrite the existing cache file. "
                                                "If you want to use the saved cache, disable this option")


class LuxCoreConfigPhotonGI(PropertyGroup):
    enabled: BoolProperty(name="Use PhotonGI cache to accelerate indirect and/or caustic light rendering. \n"
                               "Only used during final render", default=False)

    # Shared settings
    photon_maxcount: FloatProperty(name="Photon Count (Millions)", default=20, min=1, soft_max=100,
                                    precision=0, step=10,
                                    description="Max. number of photons traced (value in millions)")
    photon_maxdepth: IntProperty(name="Photon Depth", default=8, min=3, max=64,
                                  description="Max. depth of photon paths. At each bounce, a photon might be stored")
    # I use 0.049 as default because then glossy materials with default roughness (0.05) are cached
    glossinessusagethreshold: FloatProperty(name="Glossiness Threshold", default=0.049, min=0, max=1,
                                            description=PHOTONGI_GLOSSINESSTHRESH_DESC)
    
    # Indirect cache
    indirect_enabled: BoolProperty(name="Use Indirect Cache", default=True,
                                   description="Accelerates rendering of indirect light")
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
    indirect_usagethresholdscale: FloatProperty(name="Brute Force Radius Scale", default=8, min=0, precision=1,
                                                 description=PHOTONGI_INDIRECT_USAGETHRESHOLDSCALE_DESC)

    # Caustic cache
    caustic_enabled: BoolProperty(name="Use Caustic Cache", default=False,
                                  description="Accelerates rendering of caustics at the cost of blurring them")
    caustic_maxsize: FloatProperty(name="Max. Size (Millions)", default=0.1, soft_min=0.01, min=0.001, soft_max=10,
                                    precision=1, step=1,
                                    description="Max. number of photons stored in caustic cache (value in millions)")
    caustic_lookup_radius: FloatProperty(name="Lookup Radius", default=0.075, min=0.00001, subtype="DISTANCE",
                                          description=LOOKUP_RADIUS_DESC)
    caustic_normalangle: FloatProperty(name="Normal Angle", default=radians(10), min=0, max=radians(90),
                                        subtype="ANGLE", description=NORMAL_ANGLE_DESC)
    caustic_periodic_update: BoolProperty(name="Periodic Update", default=True,
                                          description="Rebuild the caustic cache periodically to clean up photon noise. "
                                                       "The step samples parameter controls how often the cache is rebuilt")
    caustic_updatespp: IntProperty(name="Step Samples", default=8, min=1,
                                   description="How often to rebuild the cache if periodic update is enabled")
    caustic_updatespp_radiusreduction: FloatProperty(name="Radius Reduction", default=96, min=1, soft_min=70,
                                                     max=99.9, soft_max=99, subtype="PERCENTAGE",
                                                     description="Shrinking factor for the lookup radius after each pass")
    caustic_updatespp_minradius: FloatProperty(name="Minimum Radius", default=0.003, min=0.00001,
                                               subtype="DISTANCE", description="Radius at which the radius reduction stops")

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
    enabled: BoolProperty(name="", default=False, description=ENVLIGHT_CACHE_DESC)
    # TODO description
    quality: FloatProperty(name="Quality", default=0.5, min=0, max=1)

    file_path: StringProperty(name="File Path", subtype="FILE_PATH",
                              description="File path to the Env. light cache file")
    save_or_overwrite: BoolProperty(name="", default=False,
                                    description="Save the cache to a file or overwrite the existing cache file. "
                                                "If you want to use the saved cache, disable this option")


class LuxCoreConfigNoiseEstimation(PropertyGroup):
    warmup: IntProperty(name="Warmup Samples", default=8, min=1,
                         description=NOISE_THRESH_WARMUP_DESC)
    step: IntProperty(name="Test Step Samples", default=32, min=1, soft_min=16,
                       description=NOISE_THRESH_STEP_DESC)


class LuxCoreConfigImageResizePolicy(PropertyGroup):
    enabled: BoolProperty(name="Use Image Resizing", default=False, description="")
    types = [
        ("MIPMAPMEM", "Auto-Scale to MipMaps", MIPMAPMEM_DESC, 0),
        ("MINMEM", "Auto-Scale to Lowest Size", MINMEM_DESC, 1),
        ("FIXED", "Uniform Scale", FIXED_DESC, 2),
    ]
    type: EnumProperty(name="Type", items=types, default="MIPMAPMEM", description="How to resize images")
    scale: FloatProperty(name="Scale", default=100, min=0, soft_max=100, precision=1, subtype="PERCENTAGE",
                         description="Scale factor. For example, with scale = 50%, a 3000x2000 pixel image is scaled to 1500x1000. "
                                     "When using auto-scaling, this value acts as a multiplier for the automatic scale")
    min_size: IntProperty(name="Min. Size (Pixels)", default=64, min=1,
                          description="Lower limit for the scale. Images will never get scaled smaller than this size")

    def convert(self):
        prefix = "scene.images.resizepolicy."
        definitions = {}

        if self.enabled:
            definitions["type"] = self.type
            definitions["scale"] = self.scale / 100
            definitions["minsize"] = self.min_size
        else:
            definitions["type"] = "NONE"

        return utils.create_props(prefix, definitions)


class LuxCoreConfig(PropertyGroup):
    """
    Main config storage class.
    Access (in ui or export) with scene.luxcore.config
    """
    
    # These settings are mostly not directly transferrable to LuxCore properties
    # They need some if/else decisions and aggregation, e.g. to build the engine name from parts
    engines = [
        ("PATH", "Pathtracing", PATH_DESC, 0),
        ("BIDIR", "Bidirectional", BIDIR_DESC, 1),
    ]
    engine: EnumProperty(name="Lighting integrator", items=engines, default="PATH")

    # Only available when tiled rendering is off (because it uses a special tiled sampler)
    samplers = [
        ("SOBOL", "Sobol", SOBOL_DESC, 0),
        ("METROPOLIS", "Metropolis", METROPOLIS_DESC, 1),
        ("RANDOM", "Random", RANDOM_DESC, 2),
    ]
    sampler: EnumProperty(name="Sampler", items=samplers, default="SOBOL")
    
    samplers_gpu = [
        ("SOBOL", "Sobol", "Best suited sampler for the GPU. " + SOBOL_DESC, 0),
        ("RANDOM", "Random", RANDOM_DESC, 1),
    ]
    sampler_gpu: EnumProperty(name="Sampler", items=samplers_gpu, default="SOBOL")
    
    def get_sampler(self):
        return self.sampler_gpu if (self.engine == "PATH" and self.device == "OCL") else self.sampler

    # SOBOL properties
    sobol_adaptive_strength: FloatProperty(name="Adaptive Strength", default=0.9, min=0, max=0.95,
                                            description=SOBOL_ADAPTIVE_STRENGTH_DESC)

    # Noise estimation (used by adaptive samplers like SOBOL and RANDOM)
    noise_estimation: PointerProperty(type=LuxCoreConfigNoiseEstimation)
    
    # Sampler pattern (used by SOBOL and RANDOM)
    sampler_patterns = [
        ("PROGRESSIVE", "Progressive", "Optimized for quick feedback, sampling 1 sample per pixel in each pass over the image", 0),
        ("CACHE_FRIENDLY", "Cache-friendly", "Optimized for faster rendering", 1),
    ]
    sampler_pattern: EnumProperty(name="Pattern", items=sampler_patterns, default="PROGRESSIVE")
    
    out_of_core_supersampling_items = [
        ("4", "4", "", 0),
        ("8", "8", "", 1),
        ("16", "16", "", 2),
        ("32", "32", "", 3),
        ("64", "64", "", 4),
    ]
    out_of_core_supersampling: EnumProperty(name="Supersampling", items=out_of_core_supersampling_items, default="16",
                                            description="Multiplier for the samples per pass")
    out_of_core_modes = [
        ("FILM", "Only Film", "Only the film (rendered pixels) is stored in CPU RAM instead of GPU RAM", 0),
        ("EVERYTHING", "Everything", "The film, image textures, meshes and other data are stored in CPU RAM if GPU RAM is not sufficient", 1),
    ]
    out_of_core_mode: EnumProperty(name="Mode", items=out_of_core_modes, default="EVERYTHING")
    out_of_core: BoolProperty(name="Out of Core", default=False, 
                              description="Enable storage of image pixels, meshes and other data in CPU RAM if GPU RAM is not sufficient. "
                                          "Enabling this option causes the scene to use more CPU RAM")

    def using_out_of_core(self):
        return self.device == "OCL" and self.out_of_core and self.out_of_core_mode == "EVERYTHING"

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
        ("CPU", "CPU", "CPU only", 0),
        # Still called OCL for historical reasons, currently it means either OpenCL or CUDA, depending on selection in addon preferences
        ("OCL", "GPU", "Use GPU(s) and optionally the CPU. You can choose between OpenCL and CUDA in the addon preferences. "
                       "You can enable/disable each device in the Devices panel below", 1),
    ]
    device: EnumProperty(name="Device", items=devices, default="CPU")
    # A trick so we can show the user that bidir can only be used on the CPU (see UI code)
    bidir_device: EnumProperty(name="Device", items=devices, default="CPU",
                               description="Bidir is only available on CPU. Switch to the Path engine if you want to render on the GPU")

    use_tiles: BoolProperty(name="Use Tiled Path (slower)", default=False, description=TILED_DESCRIPTION)
    
    def using_tiled_path(self):
        return self.engine == "PATH" and self.use_tiles

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
    filter_enabled: BoolProperty(name="Enable Pixel Filtering", default=False, description=FILTER_DESC)
    filters = [
        ("BLACKMANHARRIS", "Blackman-Harris", "Default, usually the best option", 0),
        ("MITCHELL_SS", "Mitchell", "Sharp, but can produce black ringing artifacts around bright pixels", 1),
        ("GAUSSIAN", "Gaussian", "Blurry", 2),
        ("SINC", "Sinc", "", 4),
        ("CATMULLROM", "Catmull-Rom", "", 5),
    ]
    filter: EnumProperty(name="Filter", items=filters, default="BLACKMANHARRIS",
                          description=FILTER_DESC)
    filter_width: FloatProperty(name="Filter Width", default=1.5, min=0.5, soft_max=3,
                                 description=FILTER_WIDTH_DESC, subtype="PIXEL")
    gaussian_alpha: FloatProperty(name="Gaussian Filter Alpha", default=2, min=0.1, max=10,
                                   description="Gaussian rate of falloff. Lower values give blurrier images")
    sinc_tau: FloatProperty(name="Sinc Filter Tau", default=1, min=0.01, max=8)

    # Light strategy
    light_strategy_items = [
        ("LOG_POWER", "Log Power", LOG_POWER_DESC, 0),
        ("POWER", "Power", POWER_DESC, 1),
        ("UNIFORM", "Uniform", UNIFORM_DESC, 2),
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
    filesaver_path: StringProperty(name="", subtype="DIR_PATH", description="Output path where the scene is saved")

    # Seed
    seed: IntProperty(name="Seed", default=1, min=1, description=SEED_DESC)
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

    image_resize_policy: PointerProperty(type=LuxCoreConfigImageResizePolicy)

    def using_only_lighttracing(self):
        return (self.engine == "PATH" and self.device == "CPU" and self.path.hybridbackforward_enable
                and self.path.hybridbackforward_lightpartition == 100)
