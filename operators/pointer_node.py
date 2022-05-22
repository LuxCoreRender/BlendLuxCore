import bpy
from bpy.props import StringProperty, IntProperty
from .utils import poll_node, LUXCORE_OT_set_node_tree, LUXCORE_MT_node_tree, show_nodetree


class LUXCORE_OT_pointer_unlink_node_tree(bpy.types.Operator):
    bl_idname = "luxcore.pointer_unlink_node_tree"
    bl_label = "Unlink"
    bl_description = "Unlink this node tree"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_node(context)

    def execute(self, context):
        context.node.node_tree = None
        return {"FINISHED"}


class LUXCORE_OT_pointer_set_node_tree(bpy.types.Operator, LUXCORE_OT_set_node_tree):
    """ Dropdown operator pointer node version """

    bl_idname = "luxcore.pointer_set_node_tree"

    node_tree_index: IntProperty()

    @classmethod
    def poll(cls, context):
        return poll_node(context)

    def execute(self, context):
        node_tree = bpy.data.node_groups[self.node_tree_index]
        self.set_node_tree(context.node.id_data, context.node, "node_tree", node_tree)
        return {"FINISHED"}


# This is a menu, not an operator
class LUXCORE_MT_pointer_select_node_tree(bpy.types.Menu, LUXCORE_MT_node_tree):
    """ Dropdown menu pointer version """

    bl_idname = "LUXCORE_MT_pointer_select_node_tree"
    bl_description = "Select a node tree"

    def draw(self, context):
        if not hasattr(context, "node"):
            # this shouldn't happen, because draw is only called when the menu is open
            return
        node = context.node
        assert node.bl_idname == "LuxCoreNodeTreePointer"
        self.custom_draw(node.filter, "luxcore.pointer_set_node_tree")


class LUXCORE_OT_pointer_show_node_tree(bpy.types.Operator):
    bl_idname = "luxcore.pointer_show_node_tree"
    bl_label = "Show"
    bl_description = "Switch to the node tree"

    @classmethod
    def poll(cls, context):
        return context.node and context.node.node_tree

    def execute(self, context):
        node_tree = context.node.node_tree

        if show_nodetree(context, node_tree):
            return {"FINISHED"}

        self.report({"ERROR"}, "Open a node editor first")
        return {"CANCELLED"}
