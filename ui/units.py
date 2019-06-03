# from bl_ui.properties_scene import SCENE_PT_unit
# from . import icons
#
#
# def luxcore_unit_draw(panel, context):
#     layout = panel.layout
#     scene = context.scene
#     config = scene.luxcore.config
#
#     if scene.render.engine != "LUXCORE":
#         return
#
#     col = layout.column(align=True)
#     col.prop(config, "show_min_epsilon", toggle=True)
#
#     if config.show_min_epsilon:
#         row = col.row(align=True)
#         row.prop(config, "min_epsilon")
#         row.prop(config, "max_epsilon")
#
#     if config.min_epsilon >= config.max_epsilon:
#         col.label("Min epsilon should be smaller than max epsilon!", icon=icons.WARNING)
#
#
# def register():
#     # We append our draw function to the existing Blender unit panel
#     SCENE_PT_unit.append(luxcore_unit_draw)
#
#
# def unregister():
#     SCENE_PT_unit.remove(luxcore_unit_draw)
