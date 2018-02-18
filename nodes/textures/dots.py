import bpy
from .. import LuxCoreNodeTexture
from ...utils import node as utils_node

class LuxCoreNodeTexDots(LuxCoreNodeTexture):
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
    
    def export(self, props, luxcore_name=None):        
        uvscale, uvdelta = self.inputs["2D Mapping"].export(props)

        definitions = {
            "type": "dots",
            "inside": self.inputs["Inside"].export(props),
            "outside": self.inputs["Outside"].export(props),
            # Mapping
            "mapping.type": "uvmapping2d",
            "mapping.uvscale": uvscale,
            "mapping.uvdelta": uvdelta,
        }       
        
        return self.base_export(props, definitions, luxcore_name)
