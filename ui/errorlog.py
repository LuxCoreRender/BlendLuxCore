from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from .. import utils


# Confusing, I know
ICON_ERROR = "CANCEL"
ICON_WARNING = "ERROR"


class LUXCORE_RENDER_PT_error_log(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Error Log"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        errorlog = context.scene.luxcore.errorlog
        text = "("
        icon = "NONE"
        if errorlog.errors:
            text += utils.pluralize("%d Error", len(errorlog.errors))
            icon = ICON_ERROR
        if errorlog.warnings:
            if text != "(":
                text += ", "
            text += utils.pluralize("%d Warning", len(errorlog.warnings))
            if icon == "NONE":
                icon = ICON_WARNING

        if text == "(":
            text = "(No Errors or Warnings)"
        else:
            text += ")"

        self.layout.label(text, icon)

    def draw(self, context):
        errorlog = context.scene.luxcore.errorlog

        if errorlog.errors or errorlog.warnings:
            self.layout.operator("luxcore.errorlog_clear", icon="X")

        self._draw(errorlog.errors, "Errors:", ICON_ERROR)
        self._draw(errorlog.warnings, "Warnings:", ICON_WARNING)

    def _draw(self, errors_or_warnings, label, icon="NONE"):
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
            op = row.operator("luxcore.copy_error_to_clipboard", icon="COPYDOWN")
            op.message = elem.message
