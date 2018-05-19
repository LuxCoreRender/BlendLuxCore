from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from ..utils.ui import template_refresh_button


def draw(context, layout):
    denoiser = context.scene.luxcore.denoiser
    config = context.scene.luxcore.config

    col = layout.column()

    if denoiser.enabled:
        if config.sampler == "METROPOLIS":
            col.label("Metropolis sampler can lead to artifacts!", icon="ERROR")
        if config.engine == "BIDIR" and config.filter != "NONE":
            col.label('Set filter to "None" to reduce blurriness', icon="ERROR")

    sub = col.column()
    # The user should not be able to request a refresh when denoiser is disabled
    # TODO disable the button when no final render is running - how can we detect this?
    sub.enabled = denoiser.enabled
    template_refresh_button(denoiser, "refresh", sub, "Running denoiser...")
    
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

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        denoiser = context.scene.luxcore.denoiser
        self.layout.prop(denoiser, "enabled", text="")

    def draw(self, context):
        draw(context, self.layout)

        col = self.layout.column(align=True)
        col.label("These settings are also available in the image editor tool shelf (press T)", icon="INFO")
