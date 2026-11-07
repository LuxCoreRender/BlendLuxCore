import bpy
from bpy.props import IntProperty
from ..base import LuxCoreNodeShape
from ...utils import node as utils_node


class LuxCoreNodeShapeTessellate(LuxCoreNodeShape, bpy.types.Node):
    bl_label = "Tessellate"
    bl_width_default = 150

    rate: IntProperty(
        name="Rate",
        description=(
            "Each edge of the source mesh is split into this many segments, "
            "generating rate^2 triangles per source triangle (flat tessellation)"
        ),
        default=4,
        min=1,
        update=utils_node.force_viewport_mesh_update,
    )

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        layout.prop(self, "rate")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "tessellate",
            "source": self.inputs["Shape"].export_shape(
                exporter, depsgraph, props, base_shape_name
            ),
            "rate": self.rate
        }
        return self.create_props(
            props, definitions, self.make_shape_name(base_shape_name)
        )
