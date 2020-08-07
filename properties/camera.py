import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
from bpy.types import PropertyGroup, Image
from .imagepipeline import LuxCoreImagepipeline
from .image_user import LuxCoreImageUser

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


class LuxCoreMotionBlur(PropertyGroup):
    enable: BoolProperty(name="Enable Motion Blur", default=False)
    object_blur: BoolProperty(name="Object", default=True, description="Blur moving objects")
    camera_blur: BoolProperty(name="Camera", default=False, description="Blur if camera moves")
    shutter: FloatProperty(name="Shutter (frames)", default=0.1, min=0, soft_max=2, description=SHUTTER_TIME_DESC)
    # Note: Embree allows a maximum of 129 motion steps
    steps: IntProperty(name="Steps", default=2, min=2, soft_max=20, max=129, description="Number of substeps")


class LuxCoreBokeh(PropertyGroup):
    non_uniform: BoolProperty(name="Non-Uniform Bokeh", default=False)
    blades: IntProperty(name="Blades", default=8, min=3,
                              description="Number of aperture blades")
    anisotropy: FloatProperty(name="Anisotropy", default=0, min=-1, max=1,
                                    description="Values > 0 expand the bokeh horizontally, "
                                                "values < 0 expand the bokeh vertically")
    distribution_items = [
        ("UNIFORM", "Uniform", "", 0),
        ("EXPONENTIAL", "Exponential", "", 1),
        ("INVERSEEXPONENTIAL", "Inverse Exponential", "", 2),
        ("GAUSSIAN", "Gaussian", "", 3),
        ("INVERSEGAUSSIAN", "Inverse Gaussian", "", 4),
        ("TRIANGULAR", "Triangular", "", 5),
        ("CUSTOM", "Image", "Use a custom image as bokeh distribution. Note that the image must not be totally black", 6),
    ]
    distribution: EnumProperty(name="Bokeh Distribution", items=distribution_items, default="UNIFORM")
    # The power affects only EXPONENTIAL and INVERSEEXPONENTIAL distributions
    power: IntProperty(name="Power", default=3, min=1,
                       description="Higher values lead to more pronounced exponential effects")

    def update_image(self, context):
        self.image_user.update(self.image)

    image: PointerProperty(name="Image", type=Image, update=update_image)
    image_user: PointerProperty(type=LuxCoreImageUser)


class LuxCoreCameraProps(PropertyGroup):
    use_clipping: BoolProperty(name="Clipping", default=True,
                                description="Use near/far clipping for the LuxCore camera "
                                            "(clipping still affects the Blender OpenGL viewport even if disabled)")
    use_autofocus: BoolProperty(name="Use Autofocus", default=False,
                                 description="Focus on the surface in the center of the film")
    use_clipping_plane: BoolProperty(name="Use Clipping Plane", default=False, description=CLIPPING_PLANE_DESC)
    clipping_plane: PointerProperty(name="Clipping Plane", type=bpy.types.Object, description=CLIPPING_PLANE_DESC)

    motion_blur: PointerProperty(type=LuxCoreMotionBlur)
    imagepipeline: PointerProperty(type=LuxCoreImagepipeline)
    bokeh: PointerProperty(type=LuxCoreBokeh)

    volume: PointerProperty(type=bpy.types.NodeTree)
    auto_volume: BoolProperty(name="Auto-Detect Camera Volume", default=True, description=AUTO_VOLUME_DESC)

    # Deprecated properties, we now use the Cycles properties instead.
    # Only kept for backwards compatibility reasons.
    use_dof: BoolProperty(name="Use Depth of Field", default=False)
    fstop: FloatProperty(name="F-Stop", default=2.8)
    
    @classmethod
    def register(cls):
        bpy.types.Camera.luxcore = PointerProperty(
            name="LuxCore Camera Settings",
            description="LuxCore camera settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Camera.luxcore
