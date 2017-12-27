import bpy
from bpy.props import IntProperty
from .. import LuxCoreNodeVolume


class LuxCoreNodeVolClear(LuxCoreNodeVolume):
    bl_label = "Clear Volume"
    bl_width_min = 160

    # TODO: get name, default, description etc. from super class or something
    priority = IntProperty(name="Priority", default=0, min=0)
    emission_id = IntProperty(name="Lightgroup ID", default=0, min=0)

    def init(self, context):
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketVolume", "Volume")

    def draw_buttons(self, context, layout):
        self.draw_common_buttons(context, layout)

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "clear",
        }
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
