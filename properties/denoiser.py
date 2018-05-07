from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty, IntProperty, FloatProperty,
)


class LuxCoreDenoiser(PropertyGroup):
    # TODO: descriptions
    # TODO: maybe an easy mode or some presets

    enabled = BoolProperty(name="", default=False, description="Enable/disable denoiser")

    refresh = BoolProperty(name="Run Denoiser", default=False,
                           description="Update the denoised image (takes a few seconds)")

    scales = IntProperty(name="Scales", default=3, min=1)
    hist_dist_thresh = FloatProperty(name="Histogram Distance Threshold", default=1, min=0)
    patch_radius = IntProperty(name="Patch Radius", default=1, min=1)
    search_window_radius = IntProperty(name="Search Window Radius", default=6, min=1)
