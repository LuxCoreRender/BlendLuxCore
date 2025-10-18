import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty
from ..base import LuxCoreNodeShape
from ...utils import node as utils_node


class LuxCoreNodeShapeMergeOnDistance(LuxCoreNodeShape, bpy.types.Node):
    bl_label = "Merge on Distance"
    bl_width_default = 150

    tolerance: IntProperty(
        name="Tolerance",
        description="A factor of epsilon for comparison of float values",
        default=1,
        min=1,
        update=utils_node.force_viewport_mesh_update,
    )

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        layout.prop(self, "tolerance")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "mergeondistance",
            "source": self.inputs["Shape"].export_shape(
                exporter, depsgraph, props, base_shape_name
            ),
            "tolerance": self.tolerance,
        }
        return self.create_props(
            props, definitions, self.make_shape_name(base_shape_name)
        )
