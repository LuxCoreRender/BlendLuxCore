from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from ...utils.refresh_button import template_refresh_button
from ...engine.base import LuxCoreRenderEngine
from ... import icons
from ...ui.icons import icon_manager
from ...properties.denoiser import LuxCoreDenoiser


class LUXCORE_RENDER_PT_denoiser(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "OpenImageDenoise"
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
        col.prop(context.scene.luxcore.denoiser, "enabled", text="Denoiser")

    def draw(self, context):
        config = context.scene.luxcore.config
        denoiser = context.scene.luxcore.denoiser
        
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = denoiser.enabled

        col = layout.column(align=True)
        col.enabled = denoiser.enabled and not LuxCoreRenderEngine.final_running

        sub = layout.column(align=False)
        sub.prop(denoiser, "max_memory_MB")
        sub.prop(denoiser, "albedo_specular_passthrough_mode")
        sub.prop(denoiser, "prefilter_AOVs")
        
        sub = layout.column(align=True)
        sub.enabled = denoiser.enabled
        template_refresh_button(LuxCoreDenoiser.refresh, "luxcore.request_denoiser_refresh",
                                sub, "Running denoiser...")
