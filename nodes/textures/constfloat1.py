from bpy.props import FloatProperty
from .. import LuxCoreNodeTexture


class LuxCoreNodeTexConstfloat1(LuxCoreNodeTexture):
    """ Constant float value """
    bl_label = "Constant Value"

    value = FloatProperty(name="Value", description="A constant float value")

    def init(self, context):
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def draw_buttons(self, context, layout):
        layout.prop(self, "value")

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "constfloat1",
            "value": self.value,
        }

        return self.base_export(props, definitions, luxcore_name)
