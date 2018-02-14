import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty
from bpy.types import PropertyGroup

DESC_MOTION_BLUR = "Export this object as instance if object motion blur is enabled in camera settings"


def init():
    bpy.types.Object.luxcore = PointerProperty(type=LuxCoreObjectProps)


class LuxCoreObjectProps(PropertyGroup):
    visible_to_camera = BoolProperty(name="Visible to Camera", default=True)
    enable_motion_blur = BoolProperty(name="Motion Blur", default=True, description=DESC_MOTION_BLUR)
