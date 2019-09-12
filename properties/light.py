import bpy
from bpy.props import (
    PointerProperty, EnumProperty, FloatProperty, IntProperty,
    FloatVectorProperty, BoolProperty, StringProperty
)
import math
from .ies import LuxCoreIESProps
from .image_user import LuxCoreImageUser


RGB_GAIN_DESC = (
    "The color of this light.\n"
    "Note that some lights have an inherent color, e.g. sun, sky, HDRI or textured lights.\n"
    "For those lights, their inherent color is multiplied with this color"
)

IMPORTANCE_DESCRIPTION = (
    "A hint how much processing power to spend on this "
    "light compared to other lights"
)

POWER_DESCRIPTION = (
    "Power in watt; setting 0 for both power and efficacy bypasses "
    "this feature and uses only the light gain"
)

EFFICACY_DESCRIPTION = (
    "Luminous efficacy in lumens per watt; setting 0 for both power "
    "and efficacy bypasses this feature and uses only the light gain"
)

GAMMA_DESCRIPTION = (
    "Gamma value of the image. Most HDR/EXR images use 1.0, while "
    "most JPG/PNG images use 2.2"
)

SAMPLEUPPERHEMISPHEREONLY_DESCRIPTION = (
    "Used to avoid shadows cast from below when using shadow catcher"
)

SPREAD_ANGLE_DESCRIPTION = (
    "How directional the light is emitted, set as the half-angle of the light source. "
    "Default is 90°. Smaller values mean that more light is emitted in the direction "
    "of the light and less to the sides"
)

LIGHTGROUP_DESC = "Add this light to a light group from the scene"

TURBIDITY_DESC = (
    "Amount of dust/fog/particles/smog in the air "
    "(will only affect the sun/sky color, but not add volumetric fog)"
)

VIS_INDIRECT_BASE = (
    "Visibility for indirect {type} rays. "
    "If disabled, this light will appear black in indirect bounces on {type} materials"
)
VIS_INDIRECT_DIFFUSE_DESC = VIS_INDIRECT_BASE.format(type="diffuse") + " (e.g. matte)"
VIS_INDIRECT_GLOSSY_DESC = VIS_INDIRECT_BASE.format(type="glossy") + " (e.g. glossy, roughglass, metal)"
VIS_INDIRECT_SPECULAR_DESC = VIS_INDIRECT_BASE.format(type="specular") + " (e.g. glass, mirror)"

RELSIZE_DESC = "1.0 is the apparent size of the sun when observed from earth (at mean distance of 149,600,000 km)"
THETA_DESC = "Half angle in degrees. Larger values make the light source appear larger and the shadows softer"


class LuxCoreLightProps(bpy.types.PropertyGroup):
    def update_image(self, context):
        self.image_user.update(self.image)

        if getattr(context, "light", None):
            # For spot light (toggle projection mode)
            if context.light.type == "SPOT":
                context.light.use_square = self.image is not None

    def update_is_laser(self, context):
        if getattr(context, "light", None):
            # For area light (laser can't be rectangular)
            if self.is_laser:
                context.light.shape = "SQUARE"

    use_cycles_settings: BoolProperty(default=False)

    ##############################################
    # BlendLuxCore specific properties needed to translate LuxCore light concepts to Blender
    light_types = [
        ("sun", "Sun", "Physically correct sun that emits parallel light rays and changes color with elevation", 0),
        ("distant", "Distant", "Distant star without atmosphere simulation (emits parallel light)", 1),
        ("hemi", "Hemi", "180 degree constant light source", 2),
    ]
    light_type: EnumProperty(name="Sun Type", items=light_types, default="sun")

    is_laser: BoolProperty(name="Laser", default=False, update=update_is_laser,
                            description="Laser light emitting parallel light rays")

    ##############################################
    # Generic properties shared by all light types
    gain: FloatProperty(name="Gain", default=1, min=0, precision=4, description="Brightness multiplier")
    rgb_gain: FloatVectorProperty(name="Tint", default=(1, 1, 1), min=0, max=1, subtype="COLOR",
                                   description=RGB_GAIN_DESC)
    importance: FloatProperty(name="Importance", default=1, min=0, description=IMPORTANCE_DESCRIPTION)
    lightgroup: StringProperty(name="Light Group", description=LIGHTGROUP_DESC)

    ##############################################
    # Light type specific properties (some are shared by multiple lights, noted in comments)
    # TODO: check min/max, add descriptions

    # sun, sky2
    turbidity: FloatProperty(name="Turbidity", default=2.2, min=0, max=30,
                              description=TURBIDITY_DESC)

    # sun
    relsize: FloatProperty(name="Relative Size", default=1, min=1,
                            description=RELSIZE_DESC)

    # The image property has different names on different lights:
    # infinite: file
    # mappoint: mapfile
    # projection: mapfile
    image: PointerProperty(name="Image", type=bpy.types.Image, update=update_image)
    image_user: PointerProperty(type=LuxCoreImageUser)
    gamma: FloatProperty(name="Gamma", default=1, min=0, description=GAMMA_DESCRIPTION)

    # infinite
    sampleupperhemisphereonly: BoolProperty(name="Sample Upper Hemisphere Only", default=False,
                                             description=SAMPLEUPPERHEMISPHEREONLY_DESCRIPTION)

    # point, mappoint
    radius: FloatProperty(name="Radius", default=0, min=0, subtype="DISTANCE", step=0.001,
                           description="If radius is greater than 0, a sphere light is used")

    # point, mappoint, spot, laser
    power: FloatProperty(name="Power", default=100, min=0, description=POWER_DESCRIPTION, unit='POWER')
    efficacy: FloatProperty(name="Efficacy (lm/W)", default=17, min=0, description=EFFICACY_DESCRIPTION)

    # mappoint
    ies: PointerProperty(type=LuxCoreIESProps)

    # spot
    # Note: coneangle and conedeltaangle are set with default Blender properties
    # (spot_size and spot_blend)

    # projection
    # Note: fov is set with default Blender properties

    # distant
    theta: FloatProperty(name="Size", default=10, min=0, soft_min=0.05,
                          description=THETA_DESC)

    # laser
    # Note: radius is set with default Blender properties (area light size)

    # area light emission nodes
    node_tree: PointerProperty(name="Node Tree", type=bpy.types.NodeTree)

    # sky2, sun, infinite, constantinfinite, area
    visibility_indirect_diffuse: BoolProperty(name="Diffuse", default=True, description=VIS_INDIRECT_DIFFUSE_DESC)
    visibility_indirect_glossy: BoolProperty(name="Glossy", default=True, description=VIS_INDIRECT_GLOSSY_DESC)
    visibility_indirect_specular: BoolProperty(name="Specular", default=True, description=VIS_INDIRECT_SPECULAR_DESC)

    # sky2, infinite, constantinfinite
    # TODO description
    use_envlight_cache: BoolProperty(name="Use Env. Light Cache", default=True)

    # area
    # We use unit="ROTATION" because angles are radians, so conversion is necessary for the UI
    spread_angle: FloatProperty(name="Spread Angle", default=math.pi / 2, min=0, soft_min=math.radians(5),
                                 max=math.pi / 2, subtype="ANGLE", unit="ROTATION",
                                 description=SPREAD_ANGLE_DESCRIPTION)

    @classmethod
    def register(cls):        
        bpy.types.Light.luxcore = PointerProperty(
            name="LuxCore Light Settings",
            description="LuxCore light settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Light.luxcore
