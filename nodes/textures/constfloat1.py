import bpy
from bpy.props import FloatProperty
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexConstfloat1(bpy.types.Node, LuxCoreNodeTexture):
    """ Constant float value """
    bl_label = "Constant Value"

    value: FloatProperty(update=utils_node.force_viewport_update, name="Value", description="A constant float value")

    def init(self, context):
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def draw_buttons(self, context, layout):
        layout.prop(self, "value")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "constfloat1",
            "value": self.value,
        }

        return self.create_props(props, definitions, luxcore_name)
