import bpy
from bpy.props import StringProperty, IntProperty
from .utils import (
    poll_world, init_vol_node_tree, LUXCORE_OT_set_node_tree, 
    LUXCORE_MT_node_tree, show_nodetree,
)


class LUXCORE_OT_world_new_volume_node_tree(bpy.types.Operator):
    """ Attach new node tree to world """

    bl_idname = "luxcore.world_new_volume_node_tree"
    bl_label = "New"
    bl_description = "Create a volume node tree"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_world(context)

    def execute(self, context):
        name = ""
        if context.world:
            name = context.world.name
        name += "_Volume"

        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_volume_nodes")
        init_vol_node_tree(node_tree, default_IOR=1)

        if context.world:
            context.world.luxcore.volume = node_tree

        return {"FINISHED"}


class LUXCORE_OT_world_unlink_volume_node_tree(bpy.types.Operator):
    bl_idname = "luxcore.world_unlink_volume_node_tree"
    bl_label = "Unlink"
    bl_description = "Unlink this volume node tree"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_world(context)

    def execute(self, context):
        context.world.luxcore.volume = None
        return {"FINISHED"}


class LUXCORE_OT_world_set_volume_node_tree(bpy.types.Operator, LUXCORE_OT_set_node_tree):
    """ Dropdown operator volume version """

    bl_idname = "luxcore.world_set_volume_node_tree"

    node_tree_index: IntProperty()

    @classmethod
    def poll(cls, context):
        return poll_world(context)

    def execute(self, context):
        node_tree = bpy.data.node_groups[self.node_tree_index]
        self.set_node_tree(context.world, context.world.luxcore, "volume", node_tree)
        return {"FINISHED"}


# This is a menu, not an operator
class LUXCORE_VOLUME_MT_world_select_volume_node_tree(bpy.types.Menu, LUXCORE_MT_node_tree):
    """ Dropdown menu world version """

    bl_idname = "LUXCORE_VOLUME_MT_world_select_volume_node_tree"
    bl_description = "Select a volume node tree"

    @classmethod
    def poll(cls, context):
        return poll_world(context)

    def draw(self, context):
        self.custom_draw("luxcore_volume_nodes",
                         "luxcore.world_set_volume_node_tree")


class LUXCORE_OT_world_show_volume_node_tree(bpy.types.Operator):
    bl_idname = "luxcore.world_show_volume_node_tree"
    bl_label = "Show"
    bl_description = "Switch to the node tree of this world"

    @classmethod
    def poll(cls, context):
        return context.world and context.world.luxcore.volume

    def execute(self, context):
        node_tree = context.world.luxcore.volume

        if show_nodetree(context, node_tree):
            return {"FINISHED"}

        self.report({"ERROR"}, "Open a node editor first")
        return {"CANCELLED"}


class LUXCORE_OT_world_set_ground_black(bpy.types.Operator):
    bl_idname = "luxcore.world_set_ground_black"
    bl_label = "Fix Sky Settings"
    bl_description = "Set the sky ground color in the world settings to black"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.world

    def execute(self, context):
        context.scene.world.luxcore.ground_enable = True
        context.scene.world.luxcore.ground_color = (0, 0, 0)
        return {"FINISHED"}


class LUXCORE_OT_create_sun_hemi(bpy.types.Operator):
    bl_idname = "luxcore.create_sun_hemi"
    bl_label = "Create Sun Light"
    bl_description = "Create a sun light and assign the HDRI"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return getattr(context, "world", None)

    def execute(self, context):
        light_data = bpy.data.lights.new(name="Hemi Sun", type="SUN")
        light_data.luxcore.light_type = "hemi"
        light_data.luxcore.image = context.world.luxcore.image

        light_obj = bpy.data.objects.new(name="Hemi Sun", object_data=light_data)
        context.collection.objects.link(light_obj)

        for obj in context.selected_objects:
            obj.select_set(False)
        light_obj.select_set(True)
        context.view_layer.objects.active = light_obj

        context.world.luxcore.light = "none"
        context.world.update_tag()
        return {"FINISHED"}
