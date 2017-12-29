import bl_ui
import bpy


class LuxCoreDisplaySettings(bl_ui.properties_render.RenderButtonsPanel, bpy.types.Panel):
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "LuxCore Display Settings"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        display = context.scene.luxcore.display

        layout.prop(display, "interval")
