import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
from bpy.types import PropertyGroup

FSTOP_DESC = "Camera aperture, lower values result in a brighter image"
EXPOSURE_DESC = (
    "Camera shutter time in seconds. Lower values result in a darker image. "
    "Don't forget that you can enter math formulas here, e.g. 1/100"
)
SENSITIVITY_DESC = "Camera ISO value, lower values lead to a darker image"

REINHARD_PRESCALE_DESC = ""
REINHARD_POSTSCALE_DESC = ""
REINHARD_BURN_DESC = ""

tonemapper_items = [
    ("TONEMAP_LINEAR", "Linear", "Brightness is controlled by the scale value", 0),
    ("TONEMAP_LUXLINEAR", "Camera Settings", "Use camera settings (ISO, f-stop and shuttertime)", 1),
    ("TONEMAP_REINHARD02", "Reinhard", "Non-linear tonemapper that adapts to the image brightness", 2),
]


class LuxCoreImagepipeline(PropertyGroup):
    """
    Used (and initialized) in properties/camera.py
    The UI elements are located in ui/camera.py
    """
    tonemapper = EnumProperty(name="Tonemapper", items=tonemapper_items, default="TONEMAP_LINEAR",
                              description="The tonemapper converts the image from HDR to LDR")

    # Settings for TONEMAP_LINEAR
    use_autolinear = BoolProperty(name="Auto Brightness", default=True,
                                  description="Auto-detect the optimal image brightness")
    linear_scale = FloatProperty(name="Gain", default=0.5, min=0, soft_min=0.00001, soft_max=100,
                                 description="Image brightness is multiplied with this value")

    # Settings for TONEMAP_LUXLINEAR (camera settings)
    fstop = FloatProperty(name="F-stop", default=2.8, min=0.01, description=FSTOP_DESC)
    exposure = FloatProperty(name="Shutter (s)", default=1/100, min=0, description=EXPOSURE_DESC)
    sensitivity = FloatProperty(name="ISO", default=100, min=0, soft_max=6400, description=SENSITIVITY_DESC)

    # Settings for TONEMAP_REINHARD02
    reinhard_prescale = FloatProperty(name="Pre", default=1, min=0, max=25,
                                      description=REINHARD_PRESCALE_DESC)
    reinhard_postscale = FloatProperty(name="Post", default=1.2, min=0, max=25,
                                      description=REINHARD_POSTSCALE_DESC)
    reinhard_burn = FloatProperty(name="Burn", default=6, min=0.01, max=25,
                                      description=REINHARD_BURN_DESC)
