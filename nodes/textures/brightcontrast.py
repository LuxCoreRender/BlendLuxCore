import bpy
from ..base import LuxCoreNodeTexture


class LuxCoreNodeTexBrightContrast(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Brightness/Contrast"

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", [1, 1, 1])
        self.add_input("LuxCoreSocketFloatUnbounded", "Brightness", 0)
        self.add_input("LuxCoreSocketFloatUnbounded", "Contrast", 0)

        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "brightcontrast",
            "texture": self.inputs["Color"].export(exporter, depsgraph, props),
            "brightness": self.inputs["Brightness"].export(exporter, depsgraph, props),
            "contrast": self.inputs["Contrast"].export(exporter, depsgraph, props),
        }
        return self.create_props(props, definitions, luxcore_name)
