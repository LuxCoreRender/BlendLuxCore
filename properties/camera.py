import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty
from bpy.types import PropertyGroup
from .imagepipeline import LuxCoreImagepipeline

FSTOP_DESC = "Aperture, lower values result in stronger depth of field effect"

CLIPPING_PLANE_DESC = (
    "The arbitrary clipping plane is used to clip the scene at any position and angle. "
    "It is recommended to use a plane object for better preview. "
    "The clipping plane object will not be exported"
)

SHUTTER_TIME_DESC = (
    "Amount of frames between shutter open and shutter close, higher values lead to more blur. \n"
    "A value of 1.0 blurs over the length of 1 frame, a value of 2.0 over 2 frames etc"  # no dot, Blender adds it
)

AUTO_VOLUME_DESC = "Use the exterior volume of the object in the middle of the film as camera volume"


def init():
    bpy.types.Camera.luxcore = PointerProperty(type=LuxCoreCameraProps)


class LuxCoreMotionBlur(PropertyGroup):
    """
    motion_blur.*
    """
    enable: BoolProperty(name="Enable Motion Blur", default=False)
    object_blur: BoolProperty(name="Object", default=True, description="Blur moving objects")
    camera_blur: BoolProperty(name="Camera", default=False, description="Blur if camera moves")
    shutter: FloatProperty(name="Shutter (frames)", default=0.1, min=0, soft_max=2, description=SHUTTER_TIME_DESC)
    # Note: Embree allows a maximum of 129 motion steps
    steps: IntProperty(name="Steps", default=2, min=2, soft_max=20, max=129, description="Number of substeps")


class LuxCoreCameraProps(PropertyGroup):
    use_clipping: BoolProperty(name="Clipping:", default=False,
                                description="Use near/far clipping for the LuxCore camera "
                                            "(clipping still affects the Blender OpenGL viewport even if disabled)")
    use_dof: BoolProperty(name="Use Depth of Field", default=False,
                           description="Simulate the blurring happening in real-world cameras "
                                       "when objects are out of focus")
    use_autofocus: BoolProperty(name="Use Autofocus", default=False,
                                 description="Focus on the surface in the center of the film")
    fstop: FloatProperty(name="F-stop", default=2.8, min=0.01, description=FSTOP_DESC)
    use_clipping_plane: BoolProperty(name="Use Clipping Plane:", default=False, description=CLIPPING_PLANE_DESC)
    clipping_plane: PointerProperty(name="Clipping Plane", type=bpy.types.Object, description=CLIPPING_PLANE_DESC)

    motion_blur: PointerProperty(type=LuxCoreMotionBlur)
    imagepipeline: PointerProperty(type=LuxCoreImagepipeline)

    volume: PointerProperty(type=bpy.types.NodeTree)
    auto_volume: BoolProperty(name="Auto-Detect Camera Volume", default=True, description=AUTO_VOLUME_DESC)
