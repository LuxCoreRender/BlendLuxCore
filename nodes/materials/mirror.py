import bpy
from bpy.props import FloatProperty
from .. import LuxCoreNodeMaterial
from ..sockets import LuxCoreSocketFloat

class LuxCoreNodeMatMirror(LuxCoreNodeMaterial):
    """mirror material node"""
    bl_label = "Mirror Material"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Reflection Color", (1, 1, 1))
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "mirror",
            "kr": self.inputs["Reflection Color"].export(props),
        }
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
