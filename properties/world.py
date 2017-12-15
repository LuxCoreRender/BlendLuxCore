import bpy
from bpy.props import (
    PointerProperty, EnumProperty, FloatProperty,
    FloatVectorProperty, IntProperty, BoolProperty
)
from .light import SAMPLES_DESCRIPTION, IMPORTANCE_DESCRIPTION


def init():
    bpy.types.World.luxcore = PointerProperty(type=LuxCoreWorldProps)


class LuxCoreWorldProps(bpy.types.PropertyGroup):
    lights = [
        ("sky2", "Sky", "Hosek and Wilkie sky model", 0),
        ("infinite", "HDRI", "High dynamic range image", 1),
        ("constantinfinite", "Flat Color", "Flat background color", 2),
    ]
    light = EnumProperty(name="Background", items=lights, default="sky2")

    # Generic properties shared by all background light types
    gain = FloatProperty(name="Gain", default=1, min=0, description="Brightness multiplier")
    rgb_gain = FloatVectorProperty(name="Tint", default=(1, 1, 1), min=0, max=1, subtype="COLOR")
    samples = IntProperty(name="Samples", default=-1, min=-1, description=SAMPLES_DESCRIPTION)
    importance = FloatProperty(name="Importance", default=1, min=0, description=IMPORTANCE_DESCRIPTION)
    # TODO: id

    # sky2 settings
    sun = PointerProperty(name="Sun", type=bpy.types.Object, description="Used to specify the sun direction")
    turbidity = FloatProperty(name="Turbidity", default=2.2, min=0, max=30)
    groundalbedo = FloatVectorProperty(name="Ground Albedo", default=(0.5, 0.5, 0.5), min=0, max=1, subtype="COLOR")
    ground_enable = BoolProperty(name="Use Ground Color", default=False)
    ground_color = FloatVectorProperty(name="Ground Color", default=(0.5, 0.5, 0.5), min=0, max=1, subtype="COLOR")

    # infinite
    image = PointerProperty(name="Image", type=bpy.types.Image)
    gamma = FloatProperty(name="Gamma", default=1)
    sampleupperhemisphereonly = BoolProperty(name="Sample Upper Hemisphere Only", default=False,
                                             description="Used to avoid shadows cast from below when using shadow catcher")

