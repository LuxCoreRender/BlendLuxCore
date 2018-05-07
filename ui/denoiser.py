from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel


def draw(context, layout):
    denoiser = context.scene.luxcore.denoiser

    col = layout.column()

    sub = col.column()
    # The user should not be able to request a refresh when denoiser is disabled
    # TODO disable the button when no final render is running
    sub.enabled = denoiser.enabled
    sub.prop(denoiser, "refresh", toggle=True, icon="FILE_REFRESH")
    if denoiser.refresh:
        sub.label("Running denoiser...")
    
    sub = col.column(align=True)
    # The user should be able to adjust settings even when denoiser is disabled
    sub.active = denoiser.enabled
    sub.prop(denoiser, "scales")
    sub.prop(denoiser, "hist_dist_thresh")
    sub.prop(denoiser, "patch_radius")
    sub.prop(denoiser, "search_window_radius")


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
