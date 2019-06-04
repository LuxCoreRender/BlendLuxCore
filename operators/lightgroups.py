import bpy
from bpy.props import IntProperty
# from ..properties.lightgroups import MAX_LIGHTGROUPS


class LUXCORE_OT_add_lightgroup(bpy.types.Operator):
    bl_idname = "luxcore.add_lightgroup"
    bl_label = "Add Light Group"
    bl_description = "Add a light group"
    bl_options = {"UNDO"}

    # @classmethod
    # def poll(cls, context):
    #     active_layer = context.scene.render.layers.active
    #     groups = active_layer.luxcore.lightgroups
    #     return len(groups.custom) < MAX_LIGHTGROUPS

    def execute(self, context):
        groups = context.scene.luxcore.lightgroups
        groups.add()
        return {"FINISHED"}


class LUXCORE_OT_remove_lightgroup(bpy.types.Operator):
    bl_idname = "luxcore.remove_lightgroup"
    bl_label = "Remove Light Group"
    bl_description = "Remove this light group"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        groups = context.scene.luxcore.lightgroups
        groups.remove(self.index)
        return {"FINISHED"}
