import bl_ui
import bpy


class LuxCoreErrorLog(bl_ui.properties_render.RenderButtonsPanel, bpy.types.Panel):
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "LuxCore Error Log"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        errorlog = context.scene.luxcore.errorlog
        if errorlog.errors:
            self.layout.label("(Errors)", icon="ERROR")
        else:
            self.layout.label("(No Errors)", icon="FILE_TICK")

    def draw(self, context):
        layout = self.layout
        errorlog = context.scene.luxcore.errorlog

        if errorlog.errors:
            layout.label("Errors:", icon="ERROR")
            layout.prop(errorlog, "errors")
