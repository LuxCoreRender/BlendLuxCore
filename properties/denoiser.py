from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty, IntProperty, FloatProperty,
)


class LuxCoreDenoiser(PropertyGroup):
    # TODO: descriptions
    # TODO: maybe an easy mode or some presets
    # TODO: find out which values we can kick out of the UI because they don't need adjustments (e.g. min eigen value)

    enabled = BoolProperty(name="", default=False, description="Enable/disable denoiser")
    refresh_interval = IntProperty(name="Refresh Interval (s)", default=60, min=30)

    scales = IntProperty(name="Scales", default=3, min=1)
    hist_dist_thresh = FloatProperty(name="Histogram Distance Threshold", default=1, min=0)
    patch_radius = IntProperty(name="Patch Radius", default=1, min=1)
    search_window_radius = IntProperty(name="Search Window Radius", default=6, min=1)
    # TODO hide these three?
    min_eigen_value = FloatProperty(name="Min. Eigen Value", default=1e-8, min=0, precision=1000000000)
    marked_pixels_skipping_prob = FloatProperty(name="Marked Pixels Skipping Probability", default=1, min=0, max=1)
    use_random_pixel_order = BoolProperty(name="Random Pixel Order", default=True)
