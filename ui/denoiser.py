from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel


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
        layout = self.layout
        denoiser = context.scene.luxcore.denoiser

        layout.prop(denoiser, "refresh_interval")

        col = layout.column(align=True)
        col.prop(denoiser, "scales")
        col.prop(denoiser, "hist_dist_thresh")
        col.prop(denoiser, "patch_radius")
        col.prop(denoiser, "search_window_radius")
        col.prop(denoiser, "min_eigen_value")
        col.prop(denoiser, "marked_pixels_skipping_prob", slider=True)
        col.prop(denoiser, "use_random_pixel_order")
