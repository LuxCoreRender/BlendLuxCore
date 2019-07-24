import bpy
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node

class LuxCoreNodeTexDots(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Dots"
    bl_width_default = 200
    
    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Inside", (1.0, 1.0, 1.0))
        self.add_input("LuxCoreSocketColor", "Outside", (0.0, 0.0, 0.0))
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        if not self.inputs["2D Mapping"].is_linked:
            utils_node.draw_uv_info(context, layout)
    
    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        uvscale, uvrotation, uvdelta = self.inputs["2D Mapping"].export(exporter, depsgraph, props)

        definitions = {
            "type": "dots",
            "inside": self.inputs["Inside"].export(exporter, depsgraph, props),
            "outside": self.inputs["Outside"].export(exporter, depsgraph,  props),
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.rotation": uvrotation,
            "mapping.uvdelta": uvdelta,
        }       
        
        return self.create_props(props, definitions, luxcore_name)
