import bpy
from bpy.props import BoolProperty, IntProperty, PointerProperty, StringProperty, CollectionProperty
from bpy.types import PropertyGroup
from ..operators.blender_object import LUXCORE_OT_use_proxy_switch

DESC_VISIBLE_TO_CAM = (
    "If disabled, the object will not be visible to camera rays. "
    "Note that it will still be visible in indirect light, shadows and reflections"
)
DESC_MOTION_BLUR = "Export this object as instance if object motion blur is enabled in camera settings"
DESC_USE_PROXY = "Use the object as a proxy for quick viewport response"
DESC_PROXIES = "Filepath to the high res objects used in rendering"

class LuxCoreProxyList(PropertyGroup):
    name = StringProperty()
    matIndex = IntProperty()
    filepath = StringProperty(subtype='FILE_PATH')


def init():
    bpy.types.Object.luxcore = PointerProperty(type=LuxCoreObjectProps)


class LuxCoreObjectProps(PropertyGroup):
    visible_to_camera = BoolProperty(name="Visible to Camera", default=True, description=DESC_VISIBLE_TO_CAM)
    enable_motion_blur = BoolProperty(name="Motion Blur", default=True, description=DESC_MOTION_BLUR)
    use_proxy = BoolProperty(name="Use Proxy", default=False, update=LUXCORE_OT_use_proxy_switch,description=DESC_USE_PROXY)
    proxies = CollectionProperty(name="Proxy Files", type=LuxCoreProxyList, description=DESC_PROXIES)    
