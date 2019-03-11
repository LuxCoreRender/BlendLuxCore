from bpy.props import FloatProperty
from .. import LuxCoreNodeTexture


class LuxCoreNodeTexBlackbody(LuxCoreNodeTexture):
    bl_label = "Blackbody"
    bl_width_default = 200

    temperature = FloatProperty(name="Temperature", description="Blackbody Temperature",
                                default=6500, min=0, soft_max=10000, step=10)
    
    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "temperature", slider=True)
    
    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "blackbody",
            "temperature": self.temperature,
        }       
        
        return self.create_props(props, definitions, luxcore_name)
