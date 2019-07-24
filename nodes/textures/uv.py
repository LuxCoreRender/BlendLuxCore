import bpy
from bpy.props import EnumProperty
from ..base import LuxCoreNodeTexture


class LuxCoreNodeTexUV(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "UV Test"

    def init(self, context):
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        uvscale, uvrotation, uvdelta = self.inputs["2D Mapping"].export(exporter, props)

        definitions = {
            "type": "uv",
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.rotation": uvrotation,
            "mapping.uvdelta": uvdelta,
        }

        return self.create_props(props, definitions, luxcore_name)
