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

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "constfloat1",
            "value": self.value,
        }

        return self.create_props(props, definitions, luxcore_name)
