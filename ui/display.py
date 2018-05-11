from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from ..utils.ui import template_refresh_button


class LUXCORE_RENDER_PT_display_settings(RenderButtonsPanel, Panel):
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
        row = layout.row()
        row.prop(display, "interval")
        # TODO disable the button when no final render is running
        template_refresh_button(display, "refresh", layout, "Refreshing film...")
