import bpy
from .. import LuxCoreNodeTexture
from ... import utils

class LuxCoreNodeTexDots(LuxCoreNodeTexture):
    bl_label = "Dots"
    bl_width_min = 200   
    
    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Inside", (1.0, 1.0, 1.0))
        self.add_input("LuxCoreSocketColor", "Outside", (0.0, 0.0, 0.0))
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")
    
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
