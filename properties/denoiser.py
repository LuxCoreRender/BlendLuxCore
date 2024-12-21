from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty, IntProperty, FloatProperty, EnumProperty,
)

REFRESH_DESC = (
    "Update the denoised image (takes a few seconds to minutes, "
    "progress is shown in the status bar)"
)
SCALES_DESC = (
    "Try to use more scales if the denoised image shows blotchiness "
    "(higher values increase computation time and RAM usage)"
)
HIST_DIST_THRESH_DESC = (
    "A lower value will make the output sharper while a value higher "
    "than 1.0 will make the result more blurry"
)
SEARCH_WINDOW_RADIUS_DESC = (
    "Higher values improve the denoiser result, but lead to longer computation time"
)
FILTER_SPIKES_DESC = "Filter outliers from the input samples"
MAX_MEMORY_DESC = (
    "Approximate maximum amount of memory to use in megabytes (actual memory usage "
    "may be higher). Limiting memory usage may cause slower denoising due to internally "
    "splitting the image into overlapping tiles"
)


class LuxCoreDenoiser(PropertyGroup):
    refresh = False

    enabled: BoolProperty(name="", default=True, description="Enable/disable denoiser")
    type_items = [
        ("OIDN", "OpenImageDenoise", "", 0),
    ]
    type: EnumProperty(name="Type", items=type_items, default="OIDN")

    # OIDN settings
    max_memory_MB: IntProperty(name="Max. Memory (MB)", default=6144, min=128, soft_min=1024,
                               description=MAX_MEMORY_DESC)
    albedo_specular_passthrough_modes = [
        ("REFLECT_TRANSMIT", "Reflect and Transmit", "The albedo AOV will contain reflected and transmitted colors from specular materials", 0),
        ("ONLY_REFLECT", "Reflect", "The albedo AOV will contain only reflected colors from specular materials", 1),
        ("ONLY_TRANSMIT", "Transmit", "The albedo AOV will contain only transmitted colors from specular materials", 2),
        ("NO_REFLECT_TRANSMIT", "None", "Specular materials will be a flat white in the albedo AOV", 3),
    ]
    albedo_specular_passthrough_mode: EnumProperty(name="Albedo Specular Passthrough", items=albedo_specular_passthrough_modes,
                                                  default="REFLECT_TRANSMIT", description="How to treat specular materials in the albedo AOV")
    prefilter_AOVs: BoolProperty(name="Prefilter Auxiliary AOVs", default=True,
                                 description="Denoise the albedo and avg. shading normal AOVs before using them to denoise the main image")
