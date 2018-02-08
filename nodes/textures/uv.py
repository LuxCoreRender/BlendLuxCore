from bpy.props import EnumProperty
from .. import LuxCoreNodeTexture


class LuxCoreNodeTexUV(LuxCoreNodeTexture):
    bl_label = "UV Test"

    def init(self, context):
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def export(self, props, luxcore_name=None):
        uvscale, uvdelta = self.inputs["2D Mapping"].export(props)

        definitions = {
            "type": "uv",
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.uvdelta": uvdelta,
        }

        return self.base_export(props, definitions, luxcore_name)
