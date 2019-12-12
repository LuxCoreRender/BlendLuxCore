from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from .. import utils
from . import icons


class LUXCORE_RENDER_PT_viewport_settings(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Viewport Settings"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 8

    @classmethod
    def poll(cls, context):
         return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False      

        viewport = context.scene.luxcore.viewport
        config = context.scene.luxcore.config
        luxcore_engine = config.engine

        layout.prop(viewport, "halt_time")
        layout.prop(viewport, "denoise")

        if luxcore_engine == "PATH" and not config.use_tiles and config.path.hybridbackforward_enable:
            layout.prop(viewport, "add_light_tracing")

        if luxcore_engine == "BIDIR":
            layout.prop(viewport, "use_bidir")


class LUXCORE_RENDER_PT_viewport_settings_advanced(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Advanced"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 8
    bl_parent_id = "LUXCORE_RENDER_PT_viewport_settings"

    @classmethod
    def poll(cls, context):
         return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        viewport = context.scene.luxcore.viewport
        config = context.scene.luxcore.config
        luxcore_engine = config.engine

        resolution_reduction_supported = not (utils.using_bidir_in_viewport(context.scene)
                                              or utils.using_hybridbackforward_in_viewport(context.scene))
        col = layout.column(align=True)
        col.enabled = resolution_reduction_supported
        col.prop(viewport, "reduce_resolution_on_edit")

        col = layout.column(align=True)
        col.enabled = viewport.reduce_resolution_on_edit and resolution_reduction_supported
        col.prop(viewport, "resolution_reduction")

        col = layout.column(align=True)
        col.prop(viewport, "pixel_size")

        col = layout.column(align=True)
        col.enabled = viewport.pixel_size != "1"
        col.prop(viewport, "mag_filter")

        if not (luxcore_engine == "BIDIR" and viewport.use_bidir):
            col = layout.column(align=True)
            col.prop(viewport, "device", text="Device",expand=False)

            if viewport.device == "OCL" and not utils.is_opencl_build():
                layout.label(text="No OpenCL support in this BlendLuxCore version", icon=icons.ERROR)
                layout.label(text="(Falling back to CPU realtime engine)")