import bpy
from bpy.props import BoolProperty
from .. import LuxCoreNode
from ..sockets import LuxCoreSocketMaterial


class luxcore_material_output(LuxCoreNode):
    """
    This is where the export starts (if the output is active).
    Only one output node should be active at any time.
    """
    bl_label = "Output"
    bl_width_min = 160

    # TODO switch all other outputs to inactive if one is activated
    # TODO make it impossible to deactivate an output (enabled -> disabled is forbidden)
    active = BoolProperty(name="Active", default=True)

    def init(self, context):
        self.inputs.new("LuxCoreSocketMaterial", "test")

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        layout.prop(self, "active")

    def export(self, properties):
        pass