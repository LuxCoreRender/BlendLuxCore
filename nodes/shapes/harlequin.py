import bpy
from ..base import LuxCoreNodeShape


class LuxCoreNodeShapeHarlequin(bpy.types.Node, LuxCoreNodeShape):
    bl_label = "Harlequin"
    bl_width_default = 150

    def init(self, context):
        self.add_input("LuxCoreSocketShape", "Shape")
        self.outputs.new("LuxCoreSocketShape", "Shape")

    def export_shape(self, exporter, depsgraph, props, base_shape_name):
        definitions = {
            "type": "harlequin",
            "source": self.inputs["Shape"].export_shape(exporter, depsgraph, props, base_shape_name),
        }
        return self.create_props(props, definitions, self.make_shape_name(base_shape_name))
