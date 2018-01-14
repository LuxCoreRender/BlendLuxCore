import bpy
from bpy.props import FloatProperty
from .. import LuxCoreNodeTexture
from ... import utils

class LuxCoreNodeTexBlackbody(LuxCoreNodeTexture):
    bl_label = "Blackbody"
    bl_width_min = 200   

    temperature = FloatProperty(name="Temperature", description="Blackbody Temperature", default=6500.0, min=0.0, soft_max=10000.0)
    
    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "temperature")
    
    def export(self, props, luxcore_name=None):        

        definitions = {
            "type": "blackbody",
            "temperature": self.temperature,
        }       
        
        return self.base_export(props, definitions, luxcore_name)
