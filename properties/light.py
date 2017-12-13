import bpy
from bpy.props import PointerProperty, EnumProperty, FloatProperty, IntProperty, FloatVectorProperty, BoolProperty, StringProperty


SAMPLES_DESCRIPTION = (
    "The number of shadow ray to trace to compute direct light "
    "for this light source.\n"
    "This property is a hint and the render engine can ignore this information.\n"
    "-1 means use the default global value."
)


def init():
    bpy.types.Lamp.luxcore = PointerProperty(type=LuxCoreLightProps)


class LuxCoreLightProps(bpy.types.PropertyGroup):
    def update_image(self, context):
        if context.lamp:
            # For spot lamp (toggle projection mode)
            context.lamp.use_square = self.image is not None

    def update_is_laser(self, context):
        if context.lamp:
            # For area lamp (laser can't be rectangular)
            if self.is_laser:
                context.lamp.shape = "SQUARE"

    ##############################################
    # BlendLuxCore specific properties needed to translate LuxCore light concepts to Blender
    sun_types = [
        ("sun", "Sun", "Sun", 0),
        ("distant", "Distant", "Distant star without atmosphere simulation (emits parallel light)", 1),
    ]
    sun_type = EnumProperty(name="Sun Type", items=sun_types, default="sun")

    is_laser = BoolProperty(name="Laser", default=False,
                            description="Switch to laser light emitting parallel light rays",
                            update=update_is_laser)

    ##############################################
    # Generic properties shared by all light types
    gain = FloatProperty(name="Gain", default=1, min=0, description="Brightness multiplier")
    rgb_gain = FloatVectorProperty(name="Tint", default=(1, 1, 1), min=0, max=1, subtype="COLOR")
    samples = IntProperty(name="Samples", default=-1, min=-1, description=SAMPLES_DESCRIPTION)
    # TODO: id

    ##############################################
    # Light type specific properties (some are shared by multiple lights, noted in comments)
    # TODO: check min/max, add descriptions

    # sun, sky2
    turbidity = FloatProperty(name="Turbidity", default=2.2, min=0, max=30)

    # sun
    relsize = FloatProperty(name="Relative Size", default=1, min=0.05)

    # sky2
    groundalbedo = FloatVectorProperty(name="Ground Albedo", default=(0.5, 0.5, 0.5), min=0, max=1, subtype="COLOR")
    ground_enable = BoolProperty(name="Use Ground Color", default=True)
    ground_color = FloatVectorProperty(name="Ground Color", default=(0.5, 0.5, 0.5), min=0, max=1)

    # The image property has different names on different lights:
    # infinite: file
    # mappoint: emission.mapfile
    # projection: mapfile
    image = PointerProperty(name="Image", type=bpy.types.Image, update=update_image)
    gamma = FloatProperty(name="Gamma", default=1)
    # Note: shift parameter not exposed (we use transformation instead)

    # infinite
    sampleupperhemisphereonly = BoolProperty(name="Sample Upper Hemisphere Only", default=False,
                                             description="Used to avoid shadows cast from below when using shadow catcher")

    # point, mappoint, spot, laser
    power = FloatProperty(name="Power (W)", default=0, min=0,
                          description="Power in watt; setting 0 for both power and efficacy bypasses "
                                      "this feature and uses only the lamp gain")

    # point, mappoint, spot, laser
    efficacy = FloatProperty(name="Efficacy (lm/W)", default=0, min=0,
                             description="Luminous efficacy in lumens per watt; setting 0 for both power "
                                         "and efficacy bypasses this feature and uses only the lamp gain")

    # mappoint
    iesfile = StringProperty(name="IES File", subtype="FILE_PATH")
    flipz = BoolProperty(name="Flip IES Z Axis", default=False)
    # not exposed: emission.map.width, emission.map.height - do we need them?

    # spot
    # Note: coneangle and conedeltaangle are set with default Blender properties
    # (spot_size and spot_blend)

    # projection
    # Note: fov is set with default Blender properties

    # distant
    theta = FloatProperty(name="Size", default=10, min=0, soft_min=0.05)

    # laser
    # Note: radius is set with default Blender properties (spot_size)
