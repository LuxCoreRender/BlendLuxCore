import bpy
from bpy.props import IntProperty, FloatProperty
from ..base import LuxCoreNodeShape


class LuxCoreNodeShapeHarlequin(bpy.types.Node, LuxCoreNodeShape):
    bl_label = "Harlequin"

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        layout.prop(self, "max_level")
        layout.prop(self, "max_edge_screen_size")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "harlequin",
            "source": self.inputs["Shape"].export_shape(exporter, depsgraph, props, base_shape_name),
        }
        return self.create_props(props, definitions, self.make_name())
