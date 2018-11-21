from bl_ui.properties_render import RENDER_PT_render
from . import icons

# Note: The main LuxCore config UI is defined in ui/config.py
# Each of the other render panels is also defined in their
# own specific files in the ui/ folder.


def luxcore_render_draw(panel, context):
    layout = panel.layout
    scene = context.scene

    if scene.render.engine != "LUXCORE":
        return

    split = layout.split(percentage=0.66, align=True)
    row = split.row(align=True)
    row.operator("luxcore.start_pyluxcoretools")
    row = split.row(align=True)
    op = row.operator("luxcore.open_website", icon=icons.URL, text="Wiki")
    op.url = "https://wiki.luxcorerender.org/BlendLuxCore_Network_Rendering"


def register():
    # We append our draw function to the existing Blender render panel
    RENDER_PT_render.append(luxcore_render_draw)


def unregister():
    RENDER_PT_render.remove(luxcore_render_draw)
