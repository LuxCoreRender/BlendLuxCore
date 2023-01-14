import bpy
from ..base import LuxCoreNodeMaterial

class LuxCoreNodeMatMirror(LuxCoreNodeMaterial, bpy.types.Node):
    """mirror material node"""
    bl_label = "Mirror Material"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Reflection Color", (1, 1, 1))
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "mirror",
            "kr": self.inputs["Reflection Color"].export(exporter, depsgraph, props),
        }
        self.export_common_inputs(exporter, depsgraph, props, definitions)
        return self.create_props(props, definitions, luxcore_name)
