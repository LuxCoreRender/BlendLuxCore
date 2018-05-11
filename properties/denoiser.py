from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty, IntProperty, FloatProperty,
)


class LuxCoreDenoiser(PropertyGroup):
    # TODO: descriptions
    # TODO: maybe an easy mode or some presets

    enabled = BoolProperty(name="", default=False, description="Enable/disable denoiser")
    show_advanced = BoolProperty(name="Show Advanced", default=False,
                                 description="Show advanced settings. They usually don't need to get tweaked")

    refresh = BoolProperty(name="Run Denoiser", default=False,
                           description="Update the denoised image (takes a few seconds to minutes, "
                                       "progress is shown in the status bar)")

    scales = IntProperty(name="Scales", default=3, min=1,
                         description="Try to use more scales if the denoised image shows blotchiness")
    hist_dist_thresh = FloatProperty(name="Histogram Distance Threshold", default=1, min=0)
    patch_radius = IntProperty(name="Patch Radius", default=1, min=1)
    search_window_radius = IntProperty(name="Search Window Radius", default=6, min=1)
    filter_spikes = BoolProperty(name="Remove Fireflies", default=False,
                                 description="Enable to filter outliers from the input samples")
