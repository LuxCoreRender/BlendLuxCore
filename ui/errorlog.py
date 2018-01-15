from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel


# Confusing, I know
ICON_ERROR = "CANCEL"
ICON_WARNING = "ERROR"
ICON_ALL_GOOD = "FILE_TICK"


class LUXCORE_RENDER_PT_error_log(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Error Log"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        errorlog = context.scene.luxcore.errorlog
        if errorlog.errors:
            self.layout.label("(Errors)", icon=ICON_ERROR)
        elif errorlog.warnings:
            self.layout.label("(Warnings)", icon=ICON_WARNING)
        else:
            self.layout.label("(No Errors)", icon=ICON_ALL_GOOD)

    def draw(self, context):
        errorlog = context.scene.luxcore.errorlog

        if errorlog.errors or errorlog.warnings:
            self.layout.operator("luxcore.errorlog_clear", icon="X")

        self._draw(errorlog.errors, "Errors:", ICON_ERROR)
        self._draw(errorlog.warnings, "Warnings:", ICON_WARNING)

    def _draw(self, errors_or_warnings, label, icon=None):
        if len(errors_or_warnings) == 0:
            return

        layout = self.layout
        col = layout.column(align=True)
        box = col.box()
        box.label(text=label)

        box = col.box()
        for elem in errors_or_warnings:
            row = box.row()
            if icon:
                row.label("", icon=icon)
            row.prop(elem, "message", text="")
