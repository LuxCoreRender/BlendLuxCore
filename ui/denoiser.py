from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from ..utils.refresh_button import template_refresh_button
from ..engine import LuxCoreRenderEngine
from . import icons


def draw(context, layout):
    denoiser = context.scene.luxcore.denoiser
    config = context.scene.luxcore.config

    col = layout.column()

    if denoiser.enabled:
        if denoiser.type == "BCD":
            if config.sampler == "METROPOLIS" and not config.use_tiles:
                col.label("Metropolis sampler can lead to artifacts!", icon=icons.WARNING)

    sub = col.column()
    # The user should not be able to request a refresh when denoiser is disabled
    sub.enabled = denoiser.enabled
    template_refresh_button(denoiser, "refresh", sub, "Running denoiser...")

    if denoiser.type == "BCD":
        sub = col.column(align=True)
        # The user should be able to adjust settings even when denoiser is disabled
        sub.active = denoiser.enabled
        sub.prop(denoiser, "filter_spikes")
        sub.prop(denoiser, "hist_dist_thresh")
        sub.prop(denoiser, "search_window_radius")
        sub.prop(denoiser, "show_advanced", toggle=True, icon=("TRIA_DOWN" if denoiser.show_advanced else "TRIA_RIGHT"))
        if denoiser.show_advanced:
            sub.prop(denoiser, "scales")
            sub.prop(denoiser, "patch_radius")


class LUXCORE_RENDER_PT_denoiser(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Denoiser"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        row = self.layout.row()
        row.enabled = not LuxCoreRenderEngine.final_running
        row.prop(context.scene.luxcore.denoiser, "enabled", text="")

    def draw(self, context):
        denoiser = context.scene.luxcore.denoiser
        layout = self.layout
        layout.active = denoiser.enabled
        row = layout.row()
        row.enabled = not LuxCoreRenderEngine.final_running
        row.prop(denoiser, "type", expand=True)

        draw(context, layout)

        col = layout.column(align=True)
        col.label("These settings are also available in the image editor tool shelf (press T)", icon=icons.INFO)
