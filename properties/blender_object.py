import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty
from bpy.types import PropertyGroup
from .hair import LuxCoreHair

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
DESC_EXCLUDE_FROM_RENDER = (
    "The object will be excluded from render. "
    "Useful if you need objects to render for other engines, but not for LuxCore"
)

class LuxCoreObjectProps(PropertyGroup):
    visible_to_camera: BoolProperty(name="Visible to Camera", default=True, description=DESC_VISIBLE_TO_CAM)
    exclude_from_render: BoolProperty(name="Exclude from Render", default=False, description=DESC_EXCLUDE_FROM_RENDER)
    enable_motion_blur: BoolProperty(name="Motion Blur", default=True, description=DESC_MOTION_BLUR)
    id: IntProperty(name="Object ID", default=-1, min=-1, soft_max=32767, description=DESC_OBJECT_ID)
    hair: PointerProperty(      name="LuxCore Hair Curve Settings",description="LuxCore hair curve settings",type=LuxCoreHair)

    @classmethod
    def register(cls):
        bpy.types.Object.luxcore = PointerProperty(
            name="LuxCore Object Settings",
            description="LuxCore object settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Object.luxcore
