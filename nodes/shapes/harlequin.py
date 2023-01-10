import bpy
from ..base import LuxCoreNodeShape


class LuxCoreNodeShapeHarlequin(LuxCoreNodeShape, bpy.types.Node):
    bl_label = "Harlequin"
    bl_width_default = 200

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.label(text="Colors each triangle differently,")
        col.label(text="outputs into vertex colors.")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "harlequin",
            "source": self.inputs["Shape"].export_shape(exporter, depsgraph, props, base_shape_name),
        }
        return self.create_props(props, definitions, self.make_shape_name(base_shape_name))
