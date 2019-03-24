import bpy
from .. import LuxCoreNodeTexture


class LuxCoreNodeTexDotProduct(LuxCoreNodeTexture):
    bl_label = "Dot Product"
    bl_width_default = 200
    
    def init(self, context):
        self.add_input("LuxCoreSocketVector", "Vector 1", (0, 0, 0))
        self.add_input("LuxCoreSocketVector", "Vector 2", (0, 0, 0))
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")
    
    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "dotproduct",
            "texture1": self.inputs["Vector 1"].export(exporter, props),
            "texture2": self.inputs["Vector 2"].export(exporter, props),
        }
        return self.create_props(props, definitions, luxcore_name)
