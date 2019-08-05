import bpy
from ..base import LuxCoreNodeTexture


class LuxCoreNodeTexRemap(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Remap"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value", 0.5)
        self.add_input("LuxCoreSocketFloatUnbounded", "Source Min", 0)
        self.add_input("LuxCoreSocketFloatUnbounded", "Source Max", 1)
        self.add_input("LuxCoreSocketFloatUnbounded", "Target Min", 0)
        self.add_input("LuxCoreSocketFloatUnbounded", "Target Max", 1)

        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "remap",
            "value": self.inputs["Value"].export(exporter, depsgraph, props),
            "sourcemin": self.inputs["Source Min"].export(exporter, depsgraph, props),
            "sourcemax": self.inputs["Source Max"].export(exporter, depsgraph, props),
            "targetmin": self.inputs["Target Min"].export(exporter, depsgraph, props),
            "targetmax": self.inputs["Target Max"].export(exporter, depsgraph, props),
        }
        return self.create_props(props, definitions, luxcore_name)
