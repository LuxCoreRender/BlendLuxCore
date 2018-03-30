import bpy
from bpy.props import FloatProperty
from .. import LuxCoreNodeMaterial
from ...utils import node as utils_node

class LuxCoreNodeMatMatteTranslucent(LuxCoreNodeMaterial):
    bl_label = "Matte Translucent Material"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Reflection Color", (0.5, 0.5, 0.5))
        self.add_input("LuxCoreSocketColor", "Transmission Color", (0.5, 0.5, 0.5))
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        utils_node.draw_transmission_info(self, layout)

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "mattetranslucent",
            "kr": self.inputs["Reflection Color"].export(props),
            "kt": self.inputs["Transmission Color"].export(props),
        }
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
