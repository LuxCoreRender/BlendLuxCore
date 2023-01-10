import bpy
from ..base import LuxCoreNodeMaterial
from ...utils import node as utils_node

class LuxCoreNodeMatMatteTranslucent(LuxCoreNodeMaterial, bpy.types.Node):
    bl_label = "Matte Translucent Material"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Reflection Color", (0.5, 0.5, 0.5))
        self.add_input("LuxCoreSocketColor", "Transmission Color", (0.5, 0.5, 0.5))
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        utils_node.draw_transmission_info(self, layout)

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "mattetranslucent",
            "kr": self.inputs["Reflection Color"].export(exporter, depsgraph, props),
            "kt": self.inputs["Transmission Color"].export(exporter, depsgraph, props),
        }
        self.export_common_inputs(exporter, depsgraph, props, definitions)
        return self.create_props(props, definitions, luxcore_name)
