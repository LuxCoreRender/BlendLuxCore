import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty

FSTOP_DESC = (
    "Aperture, lower values result in stronger depth of field effect and "
    "brighten the image (if the camera settings tonemapper is selected)"
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
