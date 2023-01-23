from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from .. import icons
from ..icons import icon_manager
from ...utils.errorlog import LuxCoreErrorLog

class LUXCORE_RENDER_PT_error_log(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Error Log"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 110

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

        row = layout.row(align=True)
        if LuxCoreErrorLog.errors:
            row.label(text=str(len(LuxCoreErrorLog.errors)), icon=icons.ERROR)
        if LuxCoreErrorLog.warnings:
            row.label(text=str(len(LuxCoreErrorLog.warnings)), icon=icons.WARNING)

    def draw(self, context):
        if LuxCoreErrorLog.errors or LuxCoreErrorLog.warnings:
            self.layout.operator("luxcore.errorlog_clear", icon=icons.CLEAR)

        self._draw(LuxCoreErrorLog.errors, "Errors:", icons.ERROR)
        self._draw(LuxCoreErrorLog.warnings, "Warnings:", icons.WARNING)
        
    def _draw(self, errors_or_warnings, label, icon=icons.NONE):
        if len(errors_or_warnings) == 0:
            return

        layout = self.layout
        col = layout.column(align=True)
        box = col.box()
        box.label(text=label)

        box = col.box()
        for elem in errors_or_warnings:
            row = box.row()

            text = elem.message
            if elem.count > 1:
                text += str(elem.count) + "x"

            row.label(text=elem.message, icon=icon)
            if elem.obj_name:
                op = row.operator("luxcore.select_object", text="", icon=icons.OBJECT)
                op.obj_name = elem.obj_name
            op = row.operator("luxcore.copy_error_to_clipboard", icon=icons.COPY_TO_CLIPBOARD)
            op.message = elem.message
