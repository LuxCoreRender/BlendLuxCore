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


class LuxCoreDenoiser(PropertyGroup):
    enabled = BoolProperty(name="", default=False, description="Enable/disable denoiser")
    type_items = [
        ("BCD", "BCD", "Bayesian Collaborative Denoiser", 0),
        ("OIDN", "OIDN", "Intel Open Image Denoiser", 1),
    ]
    type = EnumProperty(name="Type", items=type_items, default="OIDN")
    show_advanced = BoolProperty(name="Show Advanced", default=False,
                                 description="Show advanced settings. They usually don't need to get tweaked")

    refresh = BoolProperty(name="Run Denoiser", default=False,
                           description=REFRESH_DESC)

    # BCD settings
    scales = IntProperty(name="Scales", default=3, min=1, soft_max=5,
                         description=SCALES_DESC)
    hist_dist_thresh = FloatProperty(name="Histogram Distance Threshold", default=1, min=0, soft_max=3,
                                     description=HIST_DIST_THRESH_DESC)
    # TODO: description for patch radius
    patch_radius = IntProperty(name="Patch Radius", default=1, min=1, soft_max=3)
    search_window_radius = IntProperty(name="Search Window Radius", default=6, min=1, soft_max=9,
                                       description=SEARCH_WINDOW_RADIUS_DESC)
    filter_spikes = BoolProperty(name="Remove Fireflies", default=False,
                                 description=FILTER_SPIKES_DESC)
