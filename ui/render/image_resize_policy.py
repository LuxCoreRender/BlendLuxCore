from ..icons import icon_manager
from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel

class LUXCORE_RENDER_PT_image_resize_policy(Panel, RenderButtonsPanel):
    bl_label = "Image Scaling"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 75

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(context.scene.luxcore.config.image_resize_policy, "enabled", text="")
        col = layout.column(align=True)
        col.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        resize_policy = context.scene.luxcore.config.image_resize_policy

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = resize_policy.enabled

        layout.prop(resize_policy, "type")
        layout.prop(resize_policy, "scale")
        layout.prop(resize_policy, "min_size")
