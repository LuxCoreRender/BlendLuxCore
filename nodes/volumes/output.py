import bpy
from bpy.props import BoolProperty
from ..output import LuxCoreNodeOutput, update_active


class LuxCoreNodeVolOutput(LuxCoreNodeOutput):
    """
    Volume output node.
    This is where the export starts (if the output is active).
    """
    bl_label = "Volume Output"
    bl_width_min = 160

    active = BoolProperty(name="Active", default=True, update=update_active)

    def init(self, context):
        self.inputs.new("LuxCoreSocketVolume", "Volume")
        super().init(context)

    def export(self, props, luxcore_name):
        self.inputs["Volume"].export(props, luxcore_name)