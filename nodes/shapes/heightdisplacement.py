import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty
from ..base import LuxCoreNodeShape
from ...utils import node as utils_node


class LuxCoreNodeShapeHeightDisplacement(bpy.types.Node, LuxCoreNodeShape):
    bl_label = "Height Displacement"
    bl_width_default = 150

    scale: FloatProperty(name="Scale", default=1, update=utils_node.force_viewport_mesh_update)
    offset: FloatProperty(name="Offset", default=0, update=utils_node.force_viewport_mesh_update)
    normal_smooth: BoolProperty(name="Smooth Normals", default=True, update=utils_node.force_viewport_mesh_update)

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.add_input("LuxCoreSocketFloatUnbounded", "Height", 0)
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        layout.prop(self, "scale")
        layout.prop(self, "offset")
        layout.prop(self, "normal_smooth")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "displacement",
            "source": self.inputs["Shape"].export_shape(exporter, depsgraph, props, base_shape_name),
            "map": self.inputs["Height"].export(exporter, depsgraph, props),
            "map.type": "height",
            "scale": self.scale,
            "offset": self.offset,
            "normalsmooth": self.normal_smooth,
        }
        return self.create_props(props, definitions, self.make_shape_name(base_shape_name))
