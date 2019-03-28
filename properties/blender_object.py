import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty
from bpy.types import PropertyGroup

DESC_VISIBLE_TO_CAM = (
    "If disabled, the object will not be visible to camera rays. "
    "Note that it will still be visible in indirect light, shadows and reflections"
)
DESC_MOTION_BLUR = "Export this object as instance if object motion blur is enabled in camera settings"
DESC_OBJECT_ID = (
    "ID for Object ID AOV. If -1 is set, the object name is hashed to a number and used as ID. "
    "The ID can be accessed from the Object ID node in material node trees. "
    "Note that the random IDs of LuxCore can be greater than 32767 "
    "(the ID Mask node in the compositor can't handle those numbers)"
)


def init():
    bpy.types.Object.luxcore = PointerProperty(type=LuxCoreObjectProps)


class LuxCoreObjectProps(PropertyGroup):
    visible_to_camera = BoolProperty(name="Visible to Camera", default=True, description=DESC_VISIBLE_TO_CAM)
    enable_motion_blur = BoolProperty(name="Motion Blur", default=True, description=DESC_MOTION_BLUR)
    id = IntProperty(name="Object ID", default=-1, min=-1, soft_max=32767, description=DESC_OBJECT_ID)
