import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty

FSTOP_DESC = (
    "Aperture, lower values result in stronger depth of field effect and "
    "brighten the image (if the camera settings tonemapper is selected)"
)

CLIPPING_PLANE_DESC = (
    "The arbitrary clipping plane is used to clip the scene at any position and angle. "
    "It is recommended to use a plane object for better preview. "
    "The clipping plane object will not be exported"
)


def init():
    bpy.types.Camera.luxcore = PointerProperty(type=LuxCoreCameraProps)


class LuxCoreCameraProps(bpy.types.PropertyGroup):
    # TODO descriptions
    use_clipping = BoolProperty(name="Clipping:", default=False)
    use_dof = BoolProperty(name="Use Depth of Field", default=False)
    use_autofocus = BoolProperty(name="Use Autofocus", default=False,
                                 description="Focus on the surface in the center of the film")
    fstop = FloatProperty(name="F-stop", default=2.8, min=0.01, description=FSTOP_DESC)
    use_clipping_plane = BoolProperty(name="Use Clipping Plane:", default=False, description=CLIPPING_PLANE_DESC)
    clipping_plane = PointerProperty(name="Clipping Plane", type=bpy.types.Object, description=CLIPPING_PLANE_DESC)
