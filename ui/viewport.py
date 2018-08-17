from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from .. import utils


class LUXCORE_RENDER_PT_viewport_settings(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Viewport Settings"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        viewport = context.scene.luxcore.viewport

        layout.prop(viewport, "halt_time")

        row = layout.row()
        row.label("Device:")
        row.prop(viewport, "device", expand=True)

        if viewport.device == "OCL" and not utils.is_opencl_build():
            layout.label("No OpenCL support in this BlendLuxCore version", icon="CANCEL")
            layout.label("(Falling back to CPU realtime engine)")

        col = layout.column()
        col.prop(viewport, "pixel_size")
        sub = col.column()
        sub.active = viewport.pixel_size != "1"
        sub.prop(viewport, "mag_filter")
