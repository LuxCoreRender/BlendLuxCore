import bpy
from ..base import LuxCoreNodeTexture


class LuxCoreNodeTriplanar(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Triplanar mapping"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Texture 1", [0.1] * 3)
        self.add_input("LuxCoreSocketColor", "Texture 2", [0.6] * 3)
        self.add_input("LuxCoreSocketColor", "Texture 3", [0.6] * 3)

        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):

        definitions = {
            "type": "triplanar",
            "texture1": self.inputs["Texture 1"].export(exporter, depsgraph, props),
            "texture2": self.inputs["Texture 2"].export(exporter, depsgraph, props),
            "texture2": self.inputs["Texture 3"].export(exporter, depsgraph, props)
        }
        return self.create_props(props, definitions, luxcore_name)
