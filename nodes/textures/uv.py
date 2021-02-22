import bpy
from ..base import LuxCoreNodeTexture

class LuxCoreNodeTexUV(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "UV Test"

    def init(self, context):
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "uv",
        }
        definitions.update(self.inputs["2D Mapping"].export(exporter, depsgraph, props))
        return self.create_props(props, definitions, luxcore_name)
