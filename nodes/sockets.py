import bpy
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty
from . import LuxCoreNodeSocket

# The rules for socket classes are these:
# - If it is a socket that's used by more than one node, put it in this file
# - If it is only used by one node, put it in the file of that node
#   (e.g. the sigma socket of the matte material)
# Unfortunately we have to create dozens of socket types because there's no other
# way to have different min/max values or different descriptions. However, most of
# the time you only have to overwrite the default_value property of the socket.


ROUGHNESS_DESCRIPTION = "Microfacet roughness; higher values lead to more blurry reflections"
IOR_DESCRIPTION = "Index of refraction; typical values: 1.0 (air), 1.3 (water), 1.5 (glass)"


class Color:
    material = (0.39, 0.78, 0.39, 1.0)
    color_texture = (0.78, 0.78, 0.16, 1.0)
    float_texture = (0.63, 0.63, 0.63, 1.0)
    # This is a nice color. I like it.
    # (1.0, 0.4, 0.216, 1)


class LuxCoreSocketMaterial(LuxCoreNodeSocket):
    color = Color.material


class LuxCoreSocketColor(LuxCoreNodeSocket):
    color = Color.color_texture
    default_value = FloatVectorProperty(subtype="COLOR")

    def export_default(self):
        return list(self.default_value)


class LuxCoreSocketFloat(LuxCoreNodeSocket):
    color = Color.float_texture
    default_value = FloatProperty()

    def export_default(self):
        return self.default_value


class LuxCoreSocketFloatPositive(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0)


class LuxCoreSocketFloat0to1(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0, max=1)


class LuxCoreSocketRoughness(LuxCoreSocketFloat):
    # Reflections look weird when roughness gets too small
    default_value = FloatProperty(min=0.001, soft_max=0.8, max=1, description=ROUGHNESS_DESCRIPTION)


class LuxCoreSocketIOR(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0, max=25, description=IOR_DESCRIPTION)
