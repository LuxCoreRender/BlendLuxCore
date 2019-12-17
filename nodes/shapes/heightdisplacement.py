import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty
from ..base import LuxCoreNodeShape


class LuxCoreNodeShapeHeightDisplacement(bpy.types.Node, LuxCoreNodeShape):
    bl_label = "Height Displacement"

    max_level: IntProperty(name="Max. Level", default=2, min=1)
    max_edge_screen_size: FloatProperty(name="Max. Edge Screen Size", default=0, min=0)

    scale: FloatProperty(name="Scale", default=1)
    offset: FloatProperty(name="Offset", default=0)
    normal_smooth: BoolProperty(name="Smooth Normals", default=True)

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
        return self.create_props(props, definitions, self.make_name())
