# from bl_ui.properties_render_layer import RenderLayerButtonsPanel
# from bpy.types import Panel
# from .. import utils
# from . import icons
#
#
# class LUXCORE_RENDERLAYER_PT_layers(RenderLayerButtonsPanel, Panel):
#     bl_label = "Layer List"
#     bl_options = {'HIDE_HEADER'}
#     COMPAT_ENGINES = {"LUXCORE"}
#
#     def draw(self, context):
#         layout = self.layout
#
#         scene = context.scene
#         rd = scene.render
#
#         row = layout.row()
#         col = row.column()
#         col.template_list("RENDERLAYER_UL_renderlayers", "", rd, "layers", rd.layers, "active_index", rows=2)
#
#         col = row.column()
#         sub = col.column(align=True)
#         sub.operator("scene.render_layer_add", icon='ZOOMIN', text="")
#         sub.operator("scene.render_layer_remove", icon='ZOOMOUT', text="")
#         col.prop(rd, "use_single_layer", icon_only=True)
#
#         if utils.is_valid_camera(scene.camera):
#             tonemapper = scene.camera.data.luxcore.imagepipeline.tonemapper
#             if len(context.scene.render.layers) > 1 and tonemapper.is_automatic():
#                 msg = "Auto tonemapper will cause brightness difference!"
#                 layout.label(msg, icon=icons.WARNING)
#                 layout.operator("luxcore.switch_to_camera_settings", icon=icons.CAMERA)
#
#
# class LUXCORE_RENDERLAYER_PT_layer_options(RenderLayerButtonsPanel, Panel):
#     bl_label = "Layer"
#     COMPAT_ENGINES = {"LUXCORE"}
#
#     def draw(self, context):
#         layout = self.layout
#
#         scene = context.scene
#         rl = scene.render.layers.active
#
#         split = layout.split()
#
#         col = split.column()
#         col.prop(scene, "layers", text="Scene")
#         col.prop(rl, "layers_exclude", text="Exclude")
#
#         col = split.column()
#         col.prop(rl, "layers", text="Layer")
#         #col.prop(rl, "layers_zmask", text="Mask Layer")
#
#         col.label(text="Override Material:")
#         col.prop(rl, "material_override", text="")
#
#         # TODO: we can add more useful checkboxes here, e.g. hair on/off
