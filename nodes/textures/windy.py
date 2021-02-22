import bpy
from ..base import LuxCoreNodeTexture


class LuxCoreNodeTexWindy(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Windy"
    bl_width_default = 200
    
    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")
    
    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "windy",
        }
        definitions.update(self.inputs["3D Mapping"].export(exporter, depsgraph, props))
        return self.create_props(props, definitions, luxcore_name)
