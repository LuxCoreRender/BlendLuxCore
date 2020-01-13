import bpy
from ..base import LuxCoreNodeTexture

class LuxCoreNodeTexCheckerboard2D(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "2D Checkerboard"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color 1", [0.1] * 3)
        self.add_input("LuxCoreSocketColor", "Color 2", [0.6] * 3)
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        col = layout.row()
        if not self.inputs["2D Mapping"].is_linked:
            layout.prop_search(self, "uvmap", context.object.data, "uv_layers", text="UV Map", icon='GROUP_UVS')

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        uvindex, uvscale, uvrotation, uvdelta = self.inputs["2D Mapping"].export(exporter, depsgraph, props)

        definitions = {
            "type": "checkerboard2d",
            "texture1": self.inputs["Color 1"].export(exporter, depsgraph, props),
            "texture2": self.inputs["Color 2"].export(exporter, depsgraph, props),
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.uvindex": uvindex,
            "mapping.rotation": uvrotation,
            "mapping.uvdelta": uvdelta,
        }
        return self.create_props(props, definitions, luxcore_name)
