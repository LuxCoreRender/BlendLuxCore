from bl_ui.properties_scene import SCENE_PT_unit


def luxcore_unit_draw(panel, context):
    layout = panel.layout
    scene = context.scene

    if scene.render.engine != "LUXCORE":
        return

    layout.prop(scene.luxcore.config, "show_min_epsilon", toggle=True)

    if scene.luxcore.config.show_min_epsilon:
        layout.prop(scene.luxcore.config, "min_epsilon")


# We append our draw function to the existing Blender unit panel
SCENE_PT_unit.append(luxcore_unit_draw)
