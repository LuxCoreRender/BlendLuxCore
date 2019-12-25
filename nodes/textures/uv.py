import bpy
from ..base import LuxCoreNodeTexture

class LuxCoreNodeTexUV(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "UV Test"

    def init(self, context):
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        uvindex, uvscale, uvrotation, uvdelta = self.inputs["2D Mapping"].export(exporter, depsgraph, props)

        if not self.inputs["2D Mapping"].is_linked:
            uvindex = 0

        definitions = {
            "type": "uv",
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.uvindex": uvindex,
            "mapping.rotation": uvrotation,
            "mapping.uvdelta": uvdelta,
        }

        return self.create_props(props, definitions, luxcore_name)
