import bl_ui
import bpy


class LuxCoreConfig(bl_ui.properties_render.RenderButtonsPanel, bpy.types.Panel):
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "LuxCore Config"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        layout.prop(config, "engine")
        layout.prop(config, "sampler")