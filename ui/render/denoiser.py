from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from ...utils.refresh_button import template_refresh_button
from ...engine.base import LuxCoreRenderEngine
from ... import icons
from ...ui.icons import icon_manager
from ...properties.denoiser import LuxCoreDenoiser


class LUXCORE_RENDER_PT_denoiser(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Denoiser"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 60

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))
        layout.enabled = not LuxCoreRenderEngine.final_running
        col = layout.column(align=True)
        col.prop(context.scene.luxcore.denoiser, "enabled", text="")

    def draw(self, context):
        config = context.scene.luxcore.config
        denoiser = context.scene.luxcore.denoiser
        
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = denoiser.enabled

        sub = layout.column(align=True)
        # The user should not be able to request a refresh when denoiser is disabled
        sub.enabled = denoiser.enabled
        template_refresh_button(LuxCoreDenoiser.refresh, "luxcore.request_denoiser_refresh",
                                sub, "Running denoiser...")

        col = layout.column(align=True)
        col.prop(denoiser, "type", expand=False)
        col.enabled = denoiser.enabled and not LuxCoreRenderEngine.final_running

        if denoiser.enabled and denoiser.type == "BCD":
            if config.get_sampler() == "METROPOLIS" and not config.use_tiles:
                layout.label(text="Metropolis sampler can lead to artifacts!", icon=icons.WARNING)

        if denoiser.type == "BCD":
            sub = layout.column(align=True)
            # The user should be able to adjust settings even when denoiser is disabled            
            sub.prop(denoiser, "filter_spikes")
            sub = layout.column(align=True)
            sub.prop(denoiser, "hist_dist_thresh")
            sub = layout.column(align=True)
            sub.prop(denoiser, "search_window_radius")
        elif denoiser.type == "OIDN":
            sub = layout.column(align=False)
            sub.prop(denoiser, "max_memory_MB")
            sub.prop(denoiser, "albedo_specular_passthrough_mode")
            sub.prop(denoiser, "prefilter_AOVs")


class LUXCORE_RENDER_PT_denoiser_bcd_advanced(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Advanced"
    bl_parent_id = "LUXCORE_RENDER_PT_denoiser"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        denoiser = context.scene.luxcore.denoiser
        return context.scene.render.engine == "LUXCORE" and denoiser.type == "BCD"

    def draw(self, context):
        denoiser = context.scene.luxcore.denoiser
        
        layout = self.layout
        layout.enabled = denoiser.enabled and not LuxCoreRenderEngine.final_running

        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(denoiser, "scales")
        layout.prop(denoiser, "patch_radius")


