import bpy
from bpy.types import Node, NodeSocket
import mathutils


class LuxCoreNode(Node):
    bl_label = ""

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname in ["luxcore_material_nodes"]

    def add_input(self, type, name, default):
        self.inputs.new(type, name)
        self.inputs[name].default_value = default


class LuxCoreNodeSocket(NodeSocket):
    bl_label = ""

    color = (1, 1, 1, 1)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked or not hasattr(self, "default_value"):
            layout.label(text)
        else:
            if type(self.default_value) == mathutils.Color:
                row = layout.row()
                row.alignment = "LEFT"
                row.prop(self, "default_value", text="")
                row.label(text=text)
            else:
                layout.prop(self, "default_value", text=text)

    # Socket color
    def draw_color(self, context, node):
        return self.color

    def export(self, properties):
        if self.is_linked:
            linked_node = self.links[0].from_node
            return linked_node.export(properties)
        elif hasattr(self, "default_value"):
            return self.default_value
        else:
            return None