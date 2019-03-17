import bpy
from .. import LuxCoreNodeTexture


class LuxCoreNodeTexDotProduct(LuxCoreNodeTexture):
    bl_label = "Dot Product"
    bl_width_default = 200
    
    def init(self, context):
        # TODO: new vector socket
        self.add_input("LuxCoreSocketColor", "Vector 1", (1.0, 1.0, 1.0))
        self.add_input("LuxCoreSocketColor", "Vector 2", (1.0, 1.0, 1.0))
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")
    
    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "dotproduct",
            "texture1": self.inputs["Vector 1"].export(exporter, props),
            "texture2": self.inputs["Vector 2"].export(exporter, props),
        }
        return self.create_props(props, definitions, luxcore_name)
