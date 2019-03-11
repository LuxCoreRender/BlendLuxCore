from bpy.props import EnumProperty
from .. import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexObjectID(LuxCoreNodeTexture):
    bl_label = "Object ID"
    bl_width_default = 150

    def change_mode(self, context):
        value_output = self.outputs["Value"]
        color_output = self.outputs["Color"]
        was_value_enabled = value_output.enabled

        color_output.enabled = self.mode == "objectidcolor"
        value_output.enabled = self.mode in {"objectid", "objectidnormalized"}

        utils_node.copy_links_after_socket_swap(value_output, color_output, was_value_enabled)

    mode_items = [
        ("objectidcolor", "Color", "Object ID interpreted as color", 0),
        ("objectidnormalized", "Normalized", "Object ID converted into 0..1 range", 1),
        ("objectid", "Raw", "Raw object ID (range: 0 to 0xffffffff)", 2),
    ]
    mode = EnumProperty(name="Mode", items=mode_items, default="objectidcolor",
                        update=change_mode)

    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")
        self.outputs["Value"].enabled = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": self.mode,
        }

        return self.create_props(props, definitions, luxcore_name)
