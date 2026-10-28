import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty
from ..base import LuxCoreNodeShape
from ...utils import node as utils_node


class LuxCoreNodeShapeSubdiv(LuxCoreNodeShape, bpy.types.Node):
    bl_label = "Subdivision"
    bl_width_default = 150

    max_level: IntProperty(
        name="Max. Level",
        default=2,
        min=1,
        update=utils_node.force_viewport_mesh_update,
    )
    max_edge_screen_size: FloatProperty(
        name="Max. Edge Screen Size",
        default=0,
        min=0,
        update=utils_node.force_viewport_mesh_update,
    )
    enhanced: BoolProperty(
        name="Enhanced",
        description="Evaluate the smooth subdivision limit surface with angle-based edge creases",
        default=True,
        update=utils_node.force_viewport_mesh_update,
    )
    merge_on_distance: BoolProperty(
        name="Preliminary Merge on Distance",
        description=(
            "Apply a preliminary 'merge on distance' before "
            "sudivision"
        ),
        default=True,
        update=utils_node.force_viewport_mesh_update,
    )
    sharpness_threshold: FloatProperty(
        name="Sharpness Threshold (radians)",
        description=(
            "If the angle between adjacent face normals is greater than this "
            "threshold, the shared edge is considered sharp and will be treated "
            "as such during subdivision."
            "\nENHANCED ONLY"
        ),
        default=0.521,
        min=0,
        update=utils_node.force_viewport_mesh_update,
    )
    crease_weight: FloatProperty(
        name="Crease weight (from 0.0 to 10.0)",
        description=(
            "Crease weight for sharp edges. High values make edges sharper. "
            "Should stay in [0.0, 10.0]."
            "\nENHANCED ONLY"
        ),
        default=10.0,
        min=0,
        update=utils_node.force_viewport_mesh_update,
    )

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        layout.prop(self, "max_level")
        layout.prop(self, "max_edge_screen_size")
        layout.prop(self, "enhanced")
        layout.prop(self, "merge_on_distance")
        layout.prop(self, "sharpness_threshold")
        layout.prop(self, "crease_weight")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "subdiv",
            "source": self.inputs["Shape"].export_shape(
                exporter, depsgraph, props, base_shape_name
            ),
            "maxlevel": self.max_level,
            "maxedgescreensize": self.max_edge_screen_size,
            "enhanced": self.enhanced,
            "mergebefore": self.merge_on_distance,
            "sharpnessthreshold": self.sharpness_threshold,
            "creaseweight": self.crease_weight
        }
        return self.create_props(
            props, definitions, self.make_shape_name(base_shape_name)
        )
