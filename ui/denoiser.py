from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel


def draw(context, layout):
    denoiser = context.scene.luxcore.denoiser

    # TODO replace with button
    layout.prop(denoiser, "refresh_interval")
    
    col = layout.column(align=True)
    col.prop(denoiser, "scales")
    col.prop(denoiser, "hist_dist_thresh")
    col.prop(denoiser, "patch_radius")
    col.prop(denoiser, "search_window_radius")


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
