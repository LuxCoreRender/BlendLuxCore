import bpy
from .utils import init_tex_node_tree
from bpy.props import IntProperty

from .utils import (
    poll_object, LUXCORE_OT_set_node_tree, LUXCORE_MT_node_tree, show_nodetree
)


class LUXCORE_OT_texture_show_nodetree(bpy.types.Operator):
    bl_idname = "luxcore.tex_show_nodetree"
    bl_label = "Show Nodes"
    bl_description = "Switch to the node tree of this emission texture"

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False

        return obj.data.luxcore.node_tree

    def execute(self, context):
        light = context.active_object.data
        node_tree = light.luxcore.node_tree

        if show_nodetree(context, node_tree):
            return {"FINISHED"}

        self.report({"ERROR"}, "Open a node editor first")
        return {"CANCELLED"}


class LUXCORE_OT_tex_nodetree_new(bpy.types.Operator):
    bl_idname = "luxcore.tex_nodetree_new"
    bl_label = "New"
    bl_description = "Create a texture node tree"
    bl_options = {"UNDO"}

    def execute(self, context):
        name = "Nodes_Texture"

        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_texture_nodes")
        init_tex_node_tree(node_tree)

        depsgraph = context.evaluated_depsgraph_get()
        obj = context.active_object
        depsgraph_obj = obj.evaluated_get(depsgraph)

        if obj.type == 'LIGHT' and obj.data.type == 'AREA':
            obj.data.luxcore.node_tree = node_tree
            depsgraph_obj.data.luxcore.node_tree =  node_tree

        return {"FINISHED"}

class LUXCORE_OT_texture_unlink(bpy.types.Operator):
    bl_idname = "luxcore.texture_unlink"
    bl_label = ""
    bl_description = "Unlink data-block"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        depsgraph = context.evaluated_depsgraph_get()
        obj = context.active_object
        depsgraph_obj = obj.evaluated_get(depsgraph)
        if obj:
            obj.data.luxcore.node_tree = None
            depsgraph_obj.data.luxcore.node_tree = None
        return {"FINISHED"}


class LUXCORE_OT_texture_set_node_tree(bpy.types.Operator, LUXCORE_OT_set_node_tree):
    """ Dropdown Operator Texture version """

    bl_idname = "luxcore.texture_set_node_tree"

    node_tree_index: IntProperty()

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        obj = context.active_object
        node_tree = bpy.data.node_groups[self.node_tree_index]
        self.set_node_tree(obj, obj.data.luxcore, "node_tree", node_tree)
        return {"FINISHED"}


# This is a menu, not an operator
class LUXCORE_MT_texture_select_node_tree(bpy.types.Menu, LUXCORE_MT_node_tree):
    """ Dropdown menu pointer version """

    bl_idname = "LUXCORE_MT_texture_select_node_tree"
    bl_description = "Select a node tree"

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def draw(self, context):
        self.custom_draw("luxcore_texture_nodes", "luxcore.texture_set_node_tree")
