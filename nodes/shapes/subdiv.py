import bpy
from bpy.props import IntProperty, FloatProperty
from ..base import LuxCoreNodeShape


class LuxCoreNodeShapeSubdiv(bpy.types.Node, LuxCoreNodeShape):
    bl_label = "Subdivision"

    max_level: IntProperty(name="Max. Level", default=2, min=1)
    max_edge_screen_size: FloatProperty(name="Max. Edge Screen Size", default=0, min=0)

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        layout.prop(self, "max_level")
        layout.prop(self, "max_edge_screen_size")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "subdiv",
            "source": self.inputs["Shape"].export_shape(exporter, depsgraph, props, base_shape_name),
            "maxlevel": self.max_level,
            "maxedgescreensize": self.max_edge_screen_size,
        }
        return self.create_props(props, definitions, self.make_name())