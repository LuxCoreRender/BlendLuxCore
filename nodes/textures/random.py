import bpy
from bpy.props import IntProperty
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexRandom(LuxCoreNodeTexture, bpy.types.Node):
    bl_label = "Random"
    bl_width_default = 200

    seed: IntProperty(name="Seed", default=0, min=0,
                      update=utils_node.force_viewport_update)
    
    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value", 0)
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def draw_buttons(self, context, layout):
        layout.label(text="Computationally expensive!")
        layout.prop(self, "seed")
    
    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "random",
            "texture": self.inputs["Value"].export(exporter, depsgraph, props),
            "seed": self.seed,
        }
        return self.create_props(props, definitions, luxcore_name)
