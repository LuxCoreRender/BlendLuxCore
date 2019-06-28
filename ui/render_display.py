from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from ..utils.refresh_button import template_refresh_button

class LUXCORE_RENDER_PT_display_settings(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Display Settings"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 5

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        display = context.scene.luxcore.display
        config = context.scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False

        if config.engine == "PATH" and config.use_tiles:
            box = layout.box()
            box.label(text="Tile Highlighting:")

            col = box.column(align=True)
            col.prop(display, "show_converged", text="Converged")
            col.prop(display, "show_notconverged", text="Unconverged")
            col.prop(display, "show_pending", text="Pending")

            box.prop(display, "show_passcounts")
        
        layout.prop(display, "interval")
        template_refresh_button(display, "refresh", layout, "Refreshing film...")
