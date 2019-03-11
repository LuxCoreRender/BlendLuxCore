from bpy.props import IntProperty, FloatProperty, StringProperty
from .. import LuxCoreNodeVolume, COLORDEPTH_DESC
from ...properties.light import LIGHTGROUP_DESC


class LuxCoreNodeVolClear(LuxCoreNodeVolume):
    bl_label = "Clear Volume"
    bl_width_default = 160

    # TODO: get name, default, description etc. from super class or something
    priority = IntProperty(name="Priority", default=0, min=0)
    color_depth = FloatProperty(name="Absorption Depth", default=1.0, min=0,
                                subtype="DISTANCE", unit="LENGTH",
                                description=COLORDEPTH_DESC)
    lightgroup = StringProperty(name="Light Group", description=LIGHTGROUP_DESC)

    def init(self, context):
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketVolume", "Volume")

    def draw_buttons(self, context, layout):
        self.draw_common_buttons(context, layout)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "clear",
        }
        self.export_common_inputs(exporter, props, definitions)
        return self.create_props(props, definitions, luxcore_name)
