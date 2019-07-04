from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel


class LUXCORE_RENDER_PT_post_processing(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Post Processing"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 10

    def draw(self, context):
        layout = self.layout
        render = context.scene.render

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(render, "use_compositing")
        col.prop(render, "use_sequencer")

        col = layout.column()
        col.prop(render, "dither_intensity", text="Dither", slider=True)
