from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from .. import utils
from . import icons


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
        luxcore_engine = context.scene.luxcore.config.engine

        layout.prop(viewport, "halt_time")

        split = layout.split(percentage=0.6)
        split.active = not (luxcore_engine == "BIDIR" and viewport.use_bidir)
        split.prop(viewport, "reduce_resolution_on_edit")
        sub = split.row()
        sub.active = viewport.reduce_resolution_on_edit
        sub.prop(viewport, "resolution_reduction")

        col = layout.column()
        col.prop(viewport, "pixel_size")
        sub = col.column()
        sub.active = viewport.pixel_size != "1"
        sub.prop(viewport, "mag_filter")

        layout.prop(viewport, "denoise")

        if luxcore_engine == "BIDIR":
            layout.prop(viewport, "use_bidir")

        if not (luxcore_engine == "BIDIR" and viewport.use_bidir):
            row = layout.row()
            row.label("Device:")
            row.prop(viewport, "device", expand=True)

            if viewport.device == "OCL" and not utils.is_opencl_build():
                layout.label("No OpenCL support in this BlendLuxCore version", icon=icons.ERROR)
                layout.label("(Falling back to CPU realtime engine)")
