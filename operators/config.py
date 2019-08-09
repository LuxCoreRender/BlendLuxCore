import bpy


class LUXCORE_OT_config_set_dlsc(bpy.types.Operator):
    bl_idname = "luxcore.config_set_dlsc"
    bl_label = "Use Direct Light Sampling Cache"
    bl_description = "Set DLS Cache as Light Strategy"

    def execute(self, context):
        context.scene.luxcore.config.light_strategy = 'DLS_CACHE'
        return {"FINISHED"}