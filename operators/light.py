import bpy
from bpy.props import StringProperty, IntProperty
from .utils import (
    poll_light, init_vol_node_tree, LUXCORE_OT_set_node_tree, 
    LUXCORE_MT_node_tree, show_nodetree,
)


class LUXCORE_OT_light_new_volume_node_tree(bpy.types.Operator):
    """ Attach new node tree to light """

    bl_idname = "luxcore.light_new_volume_node_tree"
    bl_label = "New"
    bl_description = "Create a volume node tree"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_light(context)

    def execute(self, context):
        name = ""
        if context.light:
            name = context.light.name
        name += "_Volume"

        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_volume_nodes")
        init_vol_node_tree(node_tree, default_IOR=1)

        if context.light:
            context.light.luxcore.volume = node_tree

        return {"FINISHED"}


class LUXCORE_OT_light_unlink_volume_node_tree(bpy.types.Operator):
    bl_idname = "luxcore.light_unlink_volume_node_tree"
    bl_label = "Unlink"
    bl_description = "Unlink this volume node tree"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_light(context)

    def execute(self, context):
        context.light.luxcore.volume = None
        return {"FINISHED"}


class LUXCORE_OT_light_set_volume_node_tree(bpy.types.Operator, LUXCORE_OT_set_node_tree):
    """ Dropdown operator volume version """

    bl_idname = "luxcore.light_set_volume_node_tree"

    node_tree_index: IntProperty()

    @classmethod
    def poll(cls, context):
        return poll_light(context)

    def execute(self, context):
        node_tree = bpy.data.node_groups[self.node_tree_index]
        self.set_node_tree(context.light, context.light.luxcore, "volume", node_tree)
        return {"FINISHED"}


# This is a menu, not an operator
class LUXCORE_VOLUME_MT_light_select_volume_node_tree(bpy.types.Menu, LUXCORE_MT_node_tree):
    """ Dropdown menu light version """

    bl_idname = "LUXCORE_VOLUME_MT_light_select_volume_node_tree"
    bl_description = "Select a volume node tree"

    @classmethod
    def poll(cls, context):
        return poll_light(context)

    def draw(self, context):
        self.custom_draw("luxcore_volume_nodes",
                         "luxcore.light_set_volume_node_tree")


class LUXCORE_OT_light_show_volume_node_tree(bpy.types.Operator):
    bl_idname = "luxcore.light_show_volume_node_tree"
    bl_label = "Show"
    bl_description = "Switch to the node tree of this light volume"

    @classmethod
    def poll(cls, context):
        return context.light and context.light.luxcore.volume

    def execute(self, context):
        node_tree = context.light.luxcore.volume

        if show_nodetree(context, node_tree):
            return {"FINISHED"}

        self.report({"ERROR"}, "Open a node editor first")
        return {"CANCELLED"}
