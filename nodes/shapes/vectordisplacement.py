import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, IntVectorProperty
from ..base import LuxCoreNodeShape
from ...utils import node as utils_node


class LuxCoreNodeShapeVectorDisplacement(bpy.types.Node, LuxCoreNodeShape):
    bl_label = "Vector Displacement"
    bl_width_default = 150

    scale: FloatProperty(name="Scale", default=1, update=utils_node.force_viewport_mesh_update)
    offset: FloatProperty(name="Offset", default=0, update=utils_node.force_viewport_mesh_update)
    normal_smooth: BoolProperty(name="Smooth Normals", default=True, update=utils_node.force_viewport_mesh_update)

    map_channels_items = [
        ("012", "0, 1, 2", "", 0),
        ("021", "0, 2, 1 (Mudbox)", "", 1),
        ("102", "1, 0, 2", "", 2),
        ("120", "1, 2, 0", "", 3),
        ("201", "2, 0, 1 (Blender)", "", 4),
        ("210", "2, 1, 0", "", 5),
    ]
    map_channels: EnumProperty(name="Map Channels", items=map_channels_items, default="201",
                               update=utils_node.force_viewport_mesh_update)

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.add_input("LuxCoreSocketColor", "Vector", (0, 0, 0))
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        layout.prop(self, "scale")
        layout.prop(self, "offset")
        layout.prop(self, "normal_smooth")
        layout.prop(self, "map_channels", text="")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "displacement",
            "source": self.inputs["Shape"].export_shape(exporter, depsgraph, props, base_shape_name),
            "map": self.inputs["Vector"].export(exporter, depsgraph, props),
            "map.type": "vector",
            "map.channels": list(map(int, tuple(self.map_channels))),
            "scale": self.scale,
            "offset": self.offset,
            "normalsmooth": self.normal_smooth,
        }
        return self.create_props(props, definitions, self.make_shape_name(base_shape_name))
