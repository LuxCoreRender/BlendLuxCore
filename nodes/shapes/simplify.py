import bpy
from bpy.props import BoolProperty, FloatProperty
from ..base import LuxCoreNodeShape
from ...utils import node as utils_node


class LuxCoreNodeShapeSimplify(bpy.types.Node, LuxCoreNodeShape):
    bl_label = "Simplify"

    target: FloatProperty(name="Target", default=25, min=0, max=100, subtype="PERCENTAGE",
                          update=utils_node.force_viewport_mesh_update)
    edge_screen_size: FloatProperty(name="Edge Screen Size", default=0, min=0, max=1,
                                    update=utils_node.force_viewport_mesh_update)
    preserve_border: BoolProperty(name="Preserve Border", default=False,
                                  update=utils_node.force_viewport_mesh_update)

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        layout.prop(self, "target")
        layout.prop(self, "edge_screen_size")
        layout.prop(self, "preserve_border")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "simplify",
            "source": self.inputs["Shape"].export_shape(exporter, depsgraph, props, base_shape_name),
            "target": self.target / 100,
            "edgescreensize": self.edge_screen_size,
            "preserveborder": self.preserve_border,
        }
        return self.create_props(props, definitions, self.make_shape_name(base_shape_name))
