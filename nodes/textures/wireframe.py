import bpy
from bpy.props import EnumProperty, FloatProperty
from ..base import LuxCoreNodeTexture
from ... import utils
from ...utils import node as utils_node


class LuxCoreNodeTexWireframe(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Wireframe"
    bl_width_default = 200

    width: FloatProperty(update=utils_node.force_viewport_update, name="Width", description="Width of line", min=0, subtype="DISTANCE", unit="LENGTH", default=0.1)
    
    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Border", (0.7, 0.7, 0.7))
        self.add_input("LuxCoreSocketColor", "Inside", (0.2, 0.2, 0.2))
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "width")
    
    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        
        definitions = {
            "type": "wireframe",
            "width": self.width,
            "border": self.inputs["Border"].export(exporter, depsgraph, props),
            "inside": self.inputs["Inside"].export(exporter, depsgraph, props),
        }

        return self.create_props(props, definitions, luxcore_name)
