import bl_ui
import bpy


class LuxCoreDisplaySettings(bl_ui.properties_render.RenderButtonsPanel, bpy.types.Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Display Settings"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        display = context.scene.luxcore.display

        layout.label("Viewport Render:")
        layout.prop(display, "viewport_halt_time")

        layout.label("Final Render:")
        layout.prop(display, "interval")
