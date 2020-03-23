import bpy
from ..base import LuxCoreNodeTexture


class LuxCoreNodeTexRandom(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Random"
    bl_width_default = 200
    
    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Seed", 0)
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")
    
    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "random",
            "texture": self.inputs["Seed"].export(exporter, depsgraph, props),
        }
        return self.create_props(props, definitions, luxcore_name)
