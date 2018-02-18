import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty
from .. import LuxCoreNodeTexture

from .. import sockets
from ... import utils

class LuxCoreNodeTexfBM(LuxCoreNodeTexture):
    bl_label = "fBM"
    bl_width_default = 200


    octaves = IntProperty(name="Octaves", default=8, min=1, max=29)
    roughness = FloatProperty(name="Roughness", default=0.5, min=0, max=1)
    
    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "octaves")
        layout.prop(self, "roughness")
    
    def export(self, props, luxcore_name=None):
        
        mapping_type, transformation = self.inputs["3D Mapping"].export(props)
       
        definitions = {
            "type": "fbm",
            "octaves": self.octaves,
            "roughness": self.roughness,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation),
        }
        
        return self.base_export(props, definitions, luxcore_name)
