import bpy
from bpy.props import (
    PointerProperty, EnumProperty, FloatProperty, IntProperty,
    FloatVectorProperty, BoolProperty, StringProperty
)
import math
from .ies import LuxCoreIESProps
from .image_user import LuxCoreImageUser
from .config import ENVLIGHT_CACHE_DESC
from ..utils.light_descriptions import (
    RGB_GAIN_DESC, IMPORTANCE_DESCRIPTION, POWER_DESCRIPTION, NORMALIZEBYCOLOR_DESCRIPTION,
    EXPOSURE_DESCRIPTION, EFFICACY_DESCRIPTION, LUMEN_DESCRIPTION, CANDELA_DESCRIPTION,
    PER_SQUARE_METER_DESCRIPTION, LUX_DESCRIPTION, GAMMA_DESCRIPTION,
    SAMPLEUPPERHEMISPHEREONLY_DESCRIPTION, SPREAD_ANGLE_DESCRIPTION, LIGHTGROUP_DESC,
    TURBIDITY_DESC, VIS_INDIRECT_BASE, VIS_INDIRECT_DIFFUSE_DESC, VIS_INDIRECT_GLOSSY_DESC,
    VIS_INDIRECT_SPECULAR_DESC, RELSIZE_DESC, THETA_DESC, NORMALIZE_DISTANT_DESC, SUN_SKY_GAIN_DESC,
)


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

    use_cycles_settings: BoolProperty(name="Use Cycles Settings", default=False)

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
    exposure: FloatProperty(name="Exposure", default=0, soft_min=-10, soft_max=10, precision=2, description=EXPOSURE_DESCRIPTION)
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

    volume: PointerProperty(type=bpy.types.NodeTree)

    ##############################################
    # Light type specific properties (some are shared by multiple lights, noted in comments)
    # TODO: check min/max, add descriptions

    # sun, sky2
    sun_sky_gain: FloatProperty(name="Gain", default=0.00002, min=0, precision=6, step=0.00001,
                                description=SUN_SKY_GAIN_DESC)
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
    light_units = [
        ("artistic", "Artistic", "Artist friendly unit using Gain and Exposure", 0),  
        ("power", "Power", "Radiant flux in Watt", 1),
        ("lumen", "Lumen", "Luminous flux in Lumen", 2),
        ("candela", "Candela", "Luminous intensity in Candela", 3),
    ]
        
    light_unit: EnumProperty(name="Unit", items=light_units, default="artistic")
    power: FloatProperty(name="Power", default=100, min=0, description=POWER_DESCRIPTION, unit='POWER')
    efficacy: FloatProperty(name="Efficacy (lm/W)", default=17, min=0, description=EFFICACY_DESCRIPTION)
    lumen: FloatProperty(name="Lumen", default=1000, min=0, description=LUMEN_DESCRIPTION)
    candela: FloatProperty(name="Candela", default=80, min=0, description=CANDELA_DESCRIPTION)
    normalizebycolor: BoolProperty(name="Normalize by Color Luminance", default=False, description=NORMALIZEBYCOLOR_DESCRIPTION)

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
    normalize_distant: BoolProperty(name="Normalize", default=True, description=NORMALIZE_DISTANT_DESC)

    # laser
    # Note: radius is set with default Blender properties (area light size)

    # area light emission nodes
    
    per_square_meter: BoolProperty(name="Per square meter", default=False, description=PER_SQUARE_METER_DESCRIPTION)
    node_tree: PointerProperty(name="Node Tree", type=bpy.types.NodeTree)

    # sky2, sun, infinite, constantinfinite, area
    visibility_indirect_diffuse: BoolProperty(name="Diffuse", default=True, description=VIS_INDIRECT_DIFFUSE_DESC)
    visibility_indirect_glossy: BoolProperty(name="Glossy", default=True, description=VIS_INDIRECT_GLOSSY_DESC)
    visibility_indirect_specular: BoolProperty(name="Specular", default=True, description=VIS_INDIRECT_SPECULAR_DESC)

    # sun indirect specular
    def update_visibility_indirect_specular(self, context):
        self["sun_visibility_indirect_specular"] = self.visibility_indirect_specular

    visibility_indirect_specular: BoolProperty(name="Specular", default=True, 
        description=VIS_INDIRECT_SPECULAR_DESC, 
        update=update_visibility_indirect_specular)

    def update_sun_visibility_indirect_specular(self, context):
        self["visibility_indirect_specular"] = self.sun_visibility_indirect_specular

    sun_visibility_indirect_specular: BoolProperty(name="Specular", default=False, 
        description=VIS_INDIRECT_SPECULAR_DESC, 
        update=update_sun_visibility_indirect_specular)

    # sky2, infinite, constantinfinite
    use_envlight_cache: BoolProperty(name="Use Env. Light Cache", default=True,
                                     description=ENVLIGHT_CACHE_DESC)

    # area
    # We use unit="ROTATION" because angles are radians, so conversion is necessary for the UI
    spread_angle: FloatProperty(name="Spread Angle", default=math.pi / 2, min=0, soft_min=math.radians(5),
                                 max=math.pi / 2, subtype="ANGLE", unit="ROTATION",
                                 description=SPREAD_ANGLE_DESCRIPTION)
    visible: BoolProperty(name="Visible", default=True,
                          description="Visibility for camera and shadow rays (does not influence "
                                      "visibility in reflections and refractions)")

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
