from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from ... import utils
from .. import icons
from ..icons import icon_manager

class LUXCORE_RENDER_PT_viewport_settings(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Viewport Render"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 100

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

        if not (luxcore_engine == "BIDIR" and viewport.use_bidir):
            col = layout.column(align=True)
            col.prop(viewport, "device", text="Device", expand=False)

            if viewport.device == "OCL" and not (utils.is_opencl_build() or utils.is_cuda_build()):
                layout.label(text="No GPU support in this BlendLuxCore version", icon=icons.ERROR)
                layout.label(text="(Falling back to CPU realtime engine)")
        
        layout.prop(viewport, "halt_time")

        if luxcore_engine == "PATH" and not config.use_tiles and config.path.hybridbackforward_enable:
            layout.prop(viewport, "add_light_tracing")

        if luxcore_engine == "BIDIR":
            layout.prop(viewport, "use_bidir")
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

class LUXCORE_RENDER_PT_viewport_settings_denoiser(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Denoiser"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "LUXCORE_RENDER_PT_viewport_settings"

    @classmethod
    def poll(cls, context):
         return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        layout.prop(context.scene.luxcore.viewport, "use_denoiser", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        viewport = context.scene.luxcore.viewport

        layout.active = viewport.use_denoiser

        can_use_optix = viewport.can_use_optix_denoiser(context)

        if not can_use_optix:
            layout.label(text="OptiX not available, using OIDN", icon=icons.INFO)

        col = layout.column()
        col.active = can_use_optix
        col.prop(viewport, "denoiser")
        
        if viewport.get_denoiser(context) == "OPTIX":
            col.prop(viewport, "min_samples")



class LUXCORE_RENDER_PT_viewport_settings_advanced(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Advanced"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "LUXCORE_RENDER_PT_viewport_settings"

    @classmethod
    def poll(cls, context):
         return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        viewport = context.scene.luxcore.viewport

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
