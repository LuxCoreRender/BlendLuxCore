import bpy
from ..base import LuxCoreNodeTexture


class LuxCoreNodeTexHSV(LuxCoreNodeTexture, bpy.types.Node):
    bl_label = "Hue Saturation Value"

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", [1, 1, 1])
        self.add_input("LuxCoreSocketFloat0to1", "Hue", 0.5)
        self.add_input("LuxCoreSocketFloat0to2", "Saturation", 1)
        self.add_input("LuxCoreSocketFloat0to2", "Value", 1)

        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "hsv",
            "texture": self.inputs["Color"].export(exporter, depsgraph, props),
            "hue": self.inputs["Hue"].export(exporter, depsgraph, props),
            "saturation": self.inputs["Saturation"].export(exporter, depsgraph, props),
            "value": self.inputs["Value"].export(exporter, depsgraph, props),
        }
        return self.create_props(props, definitions, luxcore_name)
