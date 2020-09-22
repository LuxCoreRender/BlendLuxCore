import bpy
from bpy.props import (
    PointerProperty, EnumProperty, FloatProperty,
    FloatVectorProperty, IntProperty, BoolProperty,
    StringProperty,
)
from .light import (
    RGB_GAIN_DESC, IMPORTANCE_DESCRIPTION,
    GAMMA_DESCRIPTION, SAMPLEUPPERHEMISPHEREONLY_DESCRIPTION,
    LIGHTGROUP_DESC, TURBIDITY_DESC, VIS_INDIRECT_DIFFUSE_DESC,
    VIS_INDIRECT_GLOSSY_DESC, VIS_INDIRECT_SPECULAR_DESC,
    SUN_SKY_GAIN_DESC,
)
from .image_user import LuxCoreImageUser
from .config import ENVLIGHT_CACHE_DESC

USE_SUN_GAIN_FOR_SKY_DESC = (
    "Use the gain setting of the attached sun "
    "(so you adjust both sun and sky gain at the same time)"
)

EXPOSURE_DESCRIPTION = (
    "Power-of-2 step multiplier. "
    "An EV step of 1 will double the brightness of the light"
)

SUN_DESC = (
    "If a sun is selected, the gain, turbidity and rotation from the sun are used for the sky"
)

GROUND_ALBEDO_DESC = (
    'Color of the light that is "reflected" back into the sky '
    'from the ground in the sky simulation. Only affects the sky color'
)

GROUND_ENABLE_DESC = (
    "Replace the lower half of the sky sphere with a solid color.\n"
    "Should be set to black if there are shadow catchers in the scene"
)

GROUND_COLOR_DESC = GROUND_ENABLE_DESC


class LuxCoreWorldProps(bpy.types.PropertyGroup):
    use_cycles_settings: BoolProperty(name="Use Cycles Settings", default=False)

    lights = [
        ("sky2", "Sky", "Hosek and Wilkie sky model", 0),
        ("infinite", "HDRI", "High dynamic range image", 1),
        ("constantinfinite", "Flat Color", "Flat background color", 2),
        ("none", "None", "No background light", 3),
    ]
    light: EnumProperty(name="Background", items=lights, default="sky2")

    # Generic properties shared by all background light types
    gain: FloatProperty(name="Gain", default=1, min=0, precision=4, description="Brightness multiplier")
    exposure: FloatProperty(name="Exposure", default=0, soft_min=-10, soft_max=10, precision=2, description=EXPOSURE_DESCRIPTION )
    rgb_gain: FloatVectorProperty(name="Tint", default=(1, 1, 1), min=0, max=1, subtype="COLOR",
                                   description=RGB_GAIN_DESC)
    importance: FloatProperty(name="Importance", default=1, min=0, description=IMPORTANCE_DESCRIPTION)
    lightgroup: StringProperty(name="Light Group", description=LIGHTGROUP_DESC)
    temperature: FloatProperty(name="Temperature", default=6500, min=0, soft_max=13000, step=100, precision=0,
                               description="Blackbody Temperature in Kelvin")
    color_modes = [
        ("rgb", "RGB Color", "", 0),
        ("temperature", "Temperature", "", 1),
    ]
    color_mode: EnumProperty(name="Color Mode", items=color_modes, default="rgb")

    # sky2 settings
    def poll_sun(self, obj):
        return obj.type == "LIGHT" and obj.data and obj.data.type == "SUN"

    sun: PointerProperty(name="Sun", type=bpy.types.Object,
                          poll=poll_sun,  # The poll method filters the objects in the scene
                          description=SUN_DESC)
    sun_sky_gain: FloatProperty(name="Gain", default=0.00002, min=0, precision=6, step=0.00001,
                                description=SUN_SKY_GAIN_DESC)
    # Only shown in UI when light is sky2 and a sun is attached
    use_sun_gain_for_sky: BoolProperty(name="Use Sun Gain", default=True,
                                        description=USE_SUN_GAIN_FOR_SKY_DESC)
    turbidity: FloatProperty(name="Turbidity", default=2.2, min=0, max=30,
                              description=TURBIDITY_DESC)
    groundalbedo: FloatVectorProperty(name="Ground Albedo", default=(0.5, 0.5, 0.5),
                                       min=0, max=1, subtype="COLOR",
                                       description=GROUND_ALBEDO_DESC)
    ground_enable: BoolProperty(name="Use Ground Color", default=False,
                                 description=GROUND_ENABLE_DESC)
    ground_color: FloatVectorProperty(name="Ground Color", default=(0.5, 0.5, 0.5),
                                       min=0, max=1, subtype="COLOR",
                                       description=GROUND_COLOR_DESC)

    # infinite
    def update_image(self, context):
        self.image_user.update(self.image)

    image: PointerProperty(name="Image", type=bpy.types.Image, update=update_image)
    image_user: PointerProperty(type=LuxCoreImageUser)
    gamma: FloatProperty(name="Gamma", default=1, min=0, description=GAMMA_DESCRIPTION)
    sampleupperhemisphereonly: BoolProperty(name="Sample Upper Hemisphere Only", default=False,
                                             description=SAMPLEUPPERHEMISPHEREONLY_DESCRIPTION)
    rotation: FloatProperty(name="Z Axis Rotation", default=0,
                             subtype="ANGLE", unit="ROTATION")

    # sky2, sun, infinite, constantinfinite
    visibility_indirect_diffuse: BoolProperty(name="Diffuse", default=True, description=VIS_INDIRECT_DIFFUSE_DESC)
    visibility_indirect_glossy: BoolProperty(name="Glossy", default=True, description=VIS_INDIRECT_GLOSSY_DESC)
    visibility_indirect_specular: BoolProperty(name="Specular", default=True, description=VIS_INDIRECT_SPECULAR_DESC)

    # sky2, infinite, constantinfinite
    use_envlight_cache: BoolProperty(name="Use Env. Light Cache", default=True,
                                     description=ENVLIGHT_CACHE_DESC)

    volume: PointerProperty(type=bpy.types.NodeTree)
    
    @classmethod
    def register(cls):
        bpy.types.World.luxcore = PointerProperty(
            name="LuxCore World Settings",
            description="LuxCore World settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.World.luxcore
    
