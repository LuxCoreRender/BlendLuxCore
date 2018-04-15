from bl_ui.properties_render import RENDER_PT_render

# Note: The main LuxCore config UI is defined in ui/config.py
# Each of the other render panels is also defined in their
# own specific files in the ui/ folder.


def luxcore_render_draw(panel, context):
    layout = panel.layout
    scene = context.scene

    if scene.render.engine != "LUXCORE":
        return

    layout.operator("luxcore.start_pyluxcoretools")


# We append our draw function to the existing Blender render panel
RENDER_PT_render.append(luxcore_render_draw)
