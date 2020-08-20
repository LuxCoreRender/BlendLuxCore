import bpy
from bpy.props import FloatProperty
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexDistort(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Distort"
    bl_width_default = 150
    
    strength: FloatProperty(name="Strength", default=1,
                            update=utils_node.force_viewport_update)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", (1, 1, 1))
        self.add_input("LuxCoreSocketVector", "Offset", (0, 0, 0))

        self.outputs.new("LuxCoreSocketColor", "Color")
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "strength")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "distort",
            "texture": self.inputs["Color"].export(exporter, depsgraph, props),
            "offset": self.inputs["Offset"].export(exporter, depsgraph, props),
            "strength": self.strength,
        }

        return self.create_props(props, definitions, luxcore_name)
