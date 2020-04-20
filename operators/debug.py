import bpy
from ..utils import ui as utils_ui


class LUXCORE_OT_toggle_debug_options(bpy.types.Operator):
    bl_idname = "luxcore.toggle_debug_options"
    bl_label = "Toggle LuxCore Debug Options"
    bl_description = "Toggle visibility and enabled state of LuxCore debug options"

    def execute(self, context):
        debug = context.scene.luxcore.debug
        # Toggle enabled along with visibility
        # (so if we hide the debug panel, debugging
        # is disabled automatically)
        debug.enabled = not debug.show
        debug.show = not debug.show

        utils_ui.tag_region_for_redraw(context, "PROPERTIES", "WINDOW")
        self.report({"INFO"}, "Debug " + ("enabled" if debug.enabled else "disabled"))
        return {"FINISHED"}


class LUXCORE_OT_debug_restart(bpy.types.Operator):
    bl_idname = "luxcore.debug_restart"
    bl_label = "LuxCore Debug Restart"
    bl_description = "Restart Blender and recover session"

    def execute(self, context):
        blender_exe = bpy.app.binary_path
        import subprocess
        subprocess.Popen([blender_exe, "-con", "--python-expr", "import bpy; bpy.ops.wm.recover_last_session()"])
        bpy.ops.wm.quit_blender()
        return {"FINISHED"}
