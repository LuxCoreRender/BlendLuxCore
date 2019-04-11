from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from . import icons


class LUXCORE_RENDER_PT_error_log(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Error Log"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        errorlog = context.scene.luxcore.errorlog

        row = self.layout.row(align=True)
        if errorlog.errors:
            row.label(str(len(errorlog.errors)), icon=icons.ERROR)
        if errorlog.warnings:
            row.label(str(len(errorlog.warnings)), icon=icons.WARNING)

    def draw(self, context):
        errorlog = context.scene.luxcore.errorlog

        if errorlog.errors or errorlog.warnings:
            self.layout.operator("luxcore.errorlog_clear", icon=icons.CLEAR)

        self._draw(errorlog.errors, "Errors:", icons.ERROR)
        self._draw(errorlog.warnings, "Warnings:", icons.WARNING)

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

            row.label(elem.message, icon=icon)
            if elem.obj_name:
                op = row.operator("luxcore.select_object", text="", icon=icons.OBJECT)
                op.obj_name = elem.obj_name
            op = row.operator("luxcore.copy_error_to_clipboard", icon=icons.COPY_TO_CLIPBOARD)
            op.message = elem.message
