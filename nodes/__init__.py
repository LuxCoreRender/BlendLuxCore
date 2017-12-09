import bpy
from bpy.types import Node, NodeSocket
import mathutils
from .. import utils


class LuxCoreNode(Node):
    """Base class for LuxCore nodes (material, volume and texture)"""
    bl_label = ""

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname in ["luxcore_material_nodes"]

    def add_input(self, type, name, default):
        self.inputs.new(type, name)
        self.inputs[name].default_value = default

    def make_name(self):
        node_tree = self.id_data
        name_parts = [self.name, node_tree.name, self.suffix]

        if node_tree.library:
            name_parts.append(node_tree.library.name)

        return utils.to_luxcore_name("_".join(name_parts))

    def base_export(self, props, definitions):
        luxcore_name = self.make_name()
        prefix = self.prefix + luxcore_name + "."
        props.Set(utils.create_props(prefix, definitions))
        return luxcore_name


class LuxCoreNodeMaterial(LuxCoreNode):
    """Base class for material nodes"""
    suffix = "mat"
    prefix = "scene.materials."


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

    def export_default(self):
        """
        Subclasses have to implement this method.
        It should return the default value in a form ready for the scene properties
        e.g. convert colors to a list
        """
        return None

    def export(self, props):
        if self.is_linked:
            linked_node = self.links[0].from_node
            return linked_node.export(props)
        elif hasattr(self, "default_value"):
            return self.export_default()
        else:
            return None
