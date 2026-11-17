import bpy
from bpy.props import IntProperty, BoolProperty
from ..base import LuxCoreNodeShape
from ...utils import node as utils_node


class LuxCoreNodeShapeTessellate(LuxCoreNodeShape, bpy.types.Node):
    bl_label = "Tessellate"
    bl_width_default = 150

    rate: IntProperty(
        name="Rate",
        description=(
            "Each edge of the source mesh is split into 2^rate segments, "
            "generating 4^rate triangles per source triangle (flat tessellation)"
        ),
        default=2,
        min=1,
        update=utils_node.force_viewport_mesh_update,
    )

    interpolated_normals: BoolProperty(
        name="Interpolated Normals",
        description=(
            "Interpolate the source vertex normals onto the tessellated points "
            "(smooth shading); if disabled, the tessellated mesh shades flat"
        ),
        default=True,
        update=utils_node.force_viewport_mesh_update,
    )

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        layout.prop(self, "rate")
        layout.prop(self, "interpolated_normals")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "tessellate",
            "source": self.inputs["Shape"].export_shape(
                exporter, depsgraph, props, base_shape_name
            ),
            "rate": self.rate,
            "interpolatednormals": self.interpolated_normals
        }
        return self.create_props(
            props, definitions, self.make_shape_name(base_shape_name)
        )
