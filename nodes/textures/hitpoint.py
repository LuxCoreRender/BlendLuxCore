from bpy.props import EnumProperty
from .. import LuxCoreNodeTexture


class LuxCoreNodeTexHitpoint(LuxCoreNodeTexture):
    """ Node for hitpointcolor and hitpointgrey textures """
    bl_label = "Vertex Color"

    def change_mode(self, context):
        self.outputs["Color"].enabled = self.mode == "hitpointcolor"
        self.outputs["Value"].enabled = self.mode == "hitpointgrey"

    mode_items = [
        ("hitpointcolor", "Color", "Vertex Color", 0),
        ("hitpointgrey", "Grey", "Convert color to grey", 1),
    ]
    mode = EnumProperty(name="Mode", items=mode_items, default="hitpointcolor",
                        update=change_mode)

    # Only used for hitpointgrey
    channel_items = [
        ("-1", "RGB", "RGB luminance", 0),
        ("0", "R", "Red luminance", 1),
        ("1", "G", "Green luminance", 2),
        ("2", "B", "Blue luminance", 3),
    ]
    channel = EnumProperty(name="Channel", items=channel_items, default="-1")

    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")
        self.outputs["Value"].enabled = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")

        if self.mode == "hitpointgrey":
            layout.prop(self, "channel")

    def sub_export(self, exporter, props, luxcore_name=None):
        definitions = {
            "type": self.mode,
        }

        if self.mode == "hitpointgrey":
            definitions["channel"] = self.channel

        return self.create_props(props, definitions, luxcore_name)
