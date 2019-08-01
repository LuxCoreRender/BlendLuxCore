import bpy
from ..properties.denoiser import LuxCoreDenoiser
from ..properties.display import LuxCoreDisplaySettings


class LUXCORE_OT_request_denoiser_refresh(bpy.types.Operator):
    bl_idname = "luxcore.request_denoiser_refresh"
    bl_label = "Refresh"
    bl_description = "Update the denoised image (takes a few seconds to minutes, progress is shown in the status bar)"

    def execute(self, context):
        LuxCoreDenoiser.refresh = True
        return {"FINISHED"}


class LUXCORE_OT_request_display_refresh(bpy.types.Operator):
    bl_idname = "luxcore.request_display_refresh"
    bl_label = "Refresh"
    bl_description = "Update the rendered image"

    def execute(self, context):
        LuxCoreDisplaySettings.refresh = True
        return {"FINISHED"}


class LUXCORE_OT_toggle_pause(bpy.types.Operator):
    bl_idname = "luxcore.toggle_pause"
    bl_label = ""
    bl_description = "Pause/Resume render"

    def execute(self, context):
        LuxCoreDisplaySettings.paused = not LuxCoreDisplaySettings.paused
        return {"FINISHED"}