import bpy
from bpy.props import PointerProperty, EnumProperty
from .. import LuxCoreNodeTexture
from ..sockets import LuxCoreSocketColor, LuxCoreSocketFresnel
from ...utils import node as utils_node



class LuxCoreNodeTexFresnel(LuxCoreNodeTexture):
    bl_label = "Fresnel"
    bl_width_min = 200
    
    def change_input_type(self, context):
        self.inputs['Reflection Color'].enabled = self.input_type == 'color'

    input_type_items = [
        ('color', 'Color', 'Use custom color as input'),
        ('preset', 'Preset', 'Use a Preset fresnel texture as input'),
        ('nk', 'Fresnel Texture File', 'Use a fresnel texture file as input')
    ]

    preset_items = [
                ('amorphous carbon', 'Amorphous carbon', 'amorphous carbon'),
                ('copper', 'Copper', 'copper'),
                ('gold', 'Gold', 'gold'),
                ('silver', 'Silver', 'silver'),
                ('aluminium', 'Aluminium', 'aluminium')
    ]

    
    input_type = EnumProperty(name='Type', description='Input Type', items=input_type_items, default='color',
                                        update=change_input_type)

    preset = EnumProperty(name='Preset', description='NK data presets', items=preset_items,
                                           default='aluminium')


    filepath = bpy.props.StringProperty(name='Nk File', description='Nk file path', subtype='FILE_PATH')


    def init(self, context):
        self.inputs.new("LuxCoreSocketColor", "Reflection Color")
        self.outputs.new("LuxCoreSocketFresnel", "Fresnel")

        

    def draw_buttons(self, context, layout):
        layout.prop(self, 'input_type', expand=True)
        
        if self.input_type == 'preset':
            layout.prop(self, 'preset')

        if self.input_type == 'nk':
            layout.prop(self, 'filepath')


    def export(self, props, luxcore_name=None):
        if self.input_type == 'color':
            definitions = {
                "type": "fresnelcolor",
                "kr": self.inputs["Reflection Color"].export(props),
            }
        elif self.input_type == 'preset':
            definitions = {
                "type": "fresnelpreset",
                "name": self.preset,
            }
        else:
            #Fresnel data file
            definitions = {
                "type": "fresnelsopra",
                "file": bpy.path.abspath(self.filepath),
            }
        
        return self.base_export(props, definitions, luxcore_name)
