# from bl_ui.properties_render import RenderButtonsPanel
# from bpy.types import Panel
# from ..utils.refresh_button import template_refresh_button
#
#
# class LUXCORE_RENDER_PT_display_settings(RenderButtonsPanel, Panel):
#     COMPAT_ENGINES = {"LUXCORE"}
#     bl_label = "LuxCore Display Settings"
#     bl_options = {"DEFAULT_CLOSED"}
#
#     @classmethod
#     def poll(cls, context):
#         return context.scene.render.engine == "LUXCORE"
#
#     def draw(self, context):
#         layout = self.layout
#         display = context.scene.luxcore.display
#         config = context.scene.luxcore.config
#
#         if config.engine == "PATH" and config.use_tiles:
#             box = layout.box()
#             box.label("Tile Highlighting:")
#
#             row = box.row(align=True)
#             row.prop(display, "show_converged", text="Converged")
#             row.prop(display, "show_notconverged", text="Unconverged")
#             row.prop(display, "show_pending", text="Pending")
#
#             box.prop(display, "show_passcounts")
#
#         row = layout.row()
#         row.prop(display, "interval")
#         template_refresh_button(display, "refresh", layout, "Refreshing film...")
