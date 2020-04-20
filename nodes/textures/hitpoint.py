import bpy
from bpy.props import EnumProperty, StringProperty, IntProperty
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexHitpoint(bpy.types.Node, LuxCoreNodeTexture):
    """ Node for hitpointcolor and hitpointgrey textures """
    bl_label = "Vertex Color"
    bl_width_default = 150

    def change_mode(self, context):
        value_output = self.outputs["Value"]
        color_output = self.outputs["Color"]
        was_value_enabled = value_output.enabled

        color_output.enabled = self.mode == "hitpointcolor"
        value_output.enabled = self.mode == "hitpointgrey"

        utils_node.copy_links_after_socket_swap(value_output, color_output, was_value_enabled)
        utils_node.force_viewport_update(self, context)

    def update_vcol(self, context):
        for i, e in enumerate(context.object.data.vertex_colors.keys()):
            if e == self.vcol:
                self.vcolindex = i
        utils_node.force_viewport_update(self, context)

    mode_items = [
        ("hitpointcolor", "Color", "Vertex Color", 0),
        ("hitpointgrey", "Grey", "Convert color to grey", 1),
    ]
    mode: EnumProperty(name="Mode", items=mode_items, default="hitpointcolor",
                        update=change_mode)
    vcol: StringProperty(update=update_vcol, name="Vertex Color")
    vcolindex: IntProperty(name="Vertex Color Index", default=0)

    # Only used for hitpointgrey
    channel_items = [
        ("-1", "RGB", "RGB luminance", 0),
        ("0", "R", "Red luminance", 1),
        ("1", "G", "Green luminance", 2),
        ("2", "B", "Blue luminance", 3),
    ]
    channel: EnumProperty(update=utils_node.force_viewport_update, name="Channel", items=channel_items, default="-1")

    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")
        self.outputs["Value"].enabled = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)

        if self.mode == "hitpointgrey":
            layout.prop(self, "channel", expand=True)

        layout.prop_search(self, "vcol", context.object.data, "vertex_colors", text="Vertex Color", icon='GROUP_VCOL')

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):

        definitions = {
            "type": self.mode,
        }
        if self.vcol:
            definitions["dataindex"] = self.vcolindex

        if self.mode == "hitpointgrey":
            definitions["channel"] = self.channel

        return self.create_props(props, definitions, luxcore_name)
