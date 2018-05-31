from bpy.types import Panel
from . import denoiser
from ..utils.refresh_button import template_refresh_button


class LuxCoreImagePanel:
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "LuxCore"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"


class LUXCORE_IMAGE_PT_display(Panel, LuxCoreImagePanel):
    bl_label = "Display"

    def draw(self, context):
        layout = self.layout
        display = context.scene.luxcore.display

        template_refresh_button(display, "refresh", layout, "Refreshing film...")
        layout.prop(display, "interval")


class LUXCORE_IMAGE_PT_denoiser(Panel, LuxCoreImagePanel):
    bl_label = "Denoiser"

    def draw(self, context):
        denoiser.draw(context, self.layout)

        col = self.layout.column()
        col.label("Change the pass to see the result", icon="INFO")
        if context.space_data.image:
            iuser = context.space_data.image_user
            col.template_image_layers(context.space_data.image, iuser)
