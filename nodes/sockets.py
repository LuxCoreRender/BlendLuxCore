import bpy
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty
from . import LuxCoreNodeSocket


class Color:
    material = (0.39, 0.78, 0.39, 1.0)
    color_texture = (0.78, 0.78, 0.16, 1.0)
    float_texture = (0.63, 0.63, 0.63, 1.0)

# (1.0, 0.4, 0.216, 1)

class LuxCoreSocketMaterial(LuxCoreNodeSocket):
    color = Color.material


class LuxCoreSocketColorTex(LuxCoreNodeSocket):
    color = Color.color_texture
    default_value = FloatVectorProperty(subtype="COLOR")

    def export_default(self):
        return list(self.default_value)


class LuxCoreSocketFloatTex(LuxCoreNodeSocket):
    color = Color.float_texture
    default_value = FloatProperty()

    def export_default(self):
        return self.default_value