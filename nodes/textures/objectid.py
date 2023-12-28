import bpy
from bpy.props import EnumProperty
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexObjectID(LuxCoreNodeTexture, bpy.types.Node):
    bl_label = "Object ID"
    bl_width_default = 150

    def change_mode(self, context):
        id = self.outputs.find("Value")
        value_output = self.outputs[id]
        id = self.outputs.find("Color")
        color_output = self.outputs[id]
        was_value_enabled = value_output.enabled

        color_output.enabled = self.mode == "objectidcolor"
        value_output.enabled = self.mode in {"objectid", "objectidnormalized"}

        utils_node.copy_links_after_socket_swap(value_output, color_output, was_value_enabled)
        utils_node.force_viewport_update(self, context)

    mode_items = [
        ("objectidcolor", "Color", "Object ID interpreted as color", 0),
        ("objectidnormalized", "Normalized", "Object ID converted into 0..1 range", 1),
        ("objectid", "Raw", "Raw object ID (range: 0 to 0xffffffff)", 2),
    ]
    mode: EnumProperty(name="Mode", items=mode_items, default="objectidcolor",
                        update=change_mode)

    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")
        self.outputs["Value"].enabled = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": self.mode,
        }

        return self.create_props(props, definitions, luxcore_name)
