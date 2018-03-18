import bpy
from bpy.props import (
    CollectionProperty, PointerProperty, BoolProperty,
    FloatProperty, FloatVectorProperty, StringProperty
)
from bpy.types import PropertyGroup

# OpenCL engines support 8 lightgroups
# However one group is always there (the default group), so 7 can be user-defined
MAX_LIGHTGROUPS = 8 - 1


class LuxCoreLightGroup(PropertyGroup):
    enabled = BoolProperty(default=True, description="Enable this light group")
    show_settings = BoolProperty(default=True)
    name = StringProperty(default="Default Light Group")
    gain = FloatProperty(name="Gain", default=1, min=0, description="Brightness multiplier")
    use_rgb_gain = BoolProperty(name="Color:", default=True, description="Use RGB color multiplier")
    rgb_gain = FloatVectorProperty(name="", default=(1, 1, 1), min=0, max=1, subtype="COLOR")
    use_temperature = BoolProperty(name="Temperature:", default=False,
                                   description="Use temperature multiplier")
    temperature = FloatProperty(name="Kelvin", default=4000, min=1000, max=10000, precision=0, step=10000,
                                description="Blackbody emission color in Kelvin")


# Attached to render layer
class LuxCoreLightGroupSettings(PropertyGroup):
    default = PointerProperty(type=LuxCoreLightGroup)
    custom = CollectionProperty(type=LuxCoreLightGroup)

    def add(self):
        if len(self.custom) < MAX_LIGHTGROUPS:
            new_group = self.custom.add()
            new_group.name = "Light Group %d" % len(self.custom)
            return new_group

    def remove(self, index):
        self.custom.remove(index)