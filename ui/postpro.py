# from bl_ui.properties_render import RenderButtonsPanel
# from bpy.types import Panel
#
#
# class LUXCORE_RENDER_PT_post_processing(RenderButtonsPanel, Panel):
#     COMPAT_ENGINES = {"LUXCORE"}
#     bl_label = "Post Processing"
#     bl_options = {'DEFAULT_CLOSED'}
#
#     def draw(self, context):
#         layout = self.layout
#         render = context.scene.render
#         split = layout.split()
#
#         col = split.column()
#         col.prop(render, "use_compositing")
#         col.prop(render, "use_sequencer")
#
#         col = split.column()
#         col.prop(render, "dither_intensity", text="Dither", slider=True)
