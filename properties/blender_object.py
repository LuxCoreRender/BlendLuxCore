import bpy
from bpy.props import BoolProperty, IntProperty, PointerProperty, StringProperty, CollectionProperty
from bpy.types import PropertyGroup

DESC_VISIBLE_TO_CAM = (
    "If disabled, the object will not be visible to camera rays. "
    "Note that it will still be visible in indirect light, shadows and reflections"
)
DESC_MOTION_BLUR = "Export this object as instance if object motion blur is enabled in camera settings"

def init():
    bpy.types.Object.luxcore = PointerProperty(type=LuxCoreObjectProps)


class LuxCoreObjectProps(PropertyGroup):
    visible_to_camera = BoolProperty(name="Visible to Camera", default=True, description=DESC_VISIBLE_TO_CAM)
    enable_motion_blur = BoolProperty(name="Motion Blur", default=True, description=DESC_MOTION_BLUR)
