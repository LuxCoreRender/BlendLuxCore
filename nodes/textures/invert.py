import bpy
from ..base import LuxCoreNodeTexture


class LuxCoreNodeTexInvert(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Invert"
    bl_width_default = 100

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", (1, 1, 1))

        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "subtract",
            "texture1": 1,
            "texture2": self.inputs["Color"].export(exporter, depsgraph, props),
        }

        return self.create_props(props, definitions, luxcore_name)
