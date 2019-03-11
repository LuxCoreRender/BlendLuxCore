import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty
from .. import LuxCoreNodeTexture

from .. import sockets
from ... import utils

class LuxCoreNodeTexWindy(LuxCoreNodeTexture):
    bl_label = "Windy"
    bl_width_default = 200
    
    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")
    
    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, props)
       
        definitions = {
            "type": "windy",
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }
        
        return self.create_props(props, definitions, luxcore_name)
