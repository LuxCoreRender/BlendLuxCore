import bpy
import blf
from bgl import *

handle = None


class TileStats:
    @classmethod
    def reset(cls):
        cls.width = 0
        cls.height = 0
        cls.film_width = 0
        cls.film_height = 0
        cls.pending_coords = []
        cls.pending_passcounts = []
        cls.converged_coords = []
        cls.converged_passcounts = []
        cls.notconverged_coords = []
        cls.notconverged_passcounts = []


def handler():
    context = bpy.context

    if context.scene.render.engine != "LUXCORE":
        return

    _tile_highlight(context)
    _denoiser_help_text(context)


def _tile_highlight(context):
    current_image = context.space_data.image
    if current_image is None or current_image.type != "RENDER_RESULT":
        return
    from ..engine import LuxCoreRenderEngine
    if not LuxCoreRenderEngine.final_running:
        return

    # This is a method that handles the correct translation and scale in the view
    view_to_region = context.region.view2d.view_to_region
    display = context.scene.luxcore.display

    if display.show_converged:
        passcounts = TileStats.converged_passcounts if display.show_passcounts else []
        _draw_tiles(TileStats.converged_coords, passcounts, (0, 1, 0, 1), view_to_region)

    if display.show_notconverged:
        passcounts = TileStats.notconverged_passcounts if display.show_passcounts else []
        _draw_tiles(TileStats.notconverged_coords, passcounts, (1, 0, 0, 1), view_to_region)

    if display.show_pending:
        passcounts = TileStats.pending_passcounts if display.show_passcounts else []
        _draw_tiles(TileStats.pending_coords, passcounts, (1, 1, 0, 1), view_to_region)


def _draw_tiles(coords, passcounts, color, view_to_region):
    if not coords:
        return

    glColor4f(*color)

    for i in range(len(coords) // 2):
        # Pixel coords
        x = coords[i * 2]
        y = coords[i * 2 + 1]
        width = min(TileStats.width, TileStats.film_width - x)
        height = min(TileStats.height, TileStats.film_height - y)

        # Relative coords in range 0..1
        rel_x = x / TileStats.film_width
        rel_y = y / TileStats.film_height
        rel_width = width / TileStats.film_width
        rel_height = height / TileStats.film_height

        _draw_rect(rel_x, rel_y, rel_width, rel_height, view_to_region)
        if passcounts:
            _draw_text(str(passcounts[i]), rel_x, rel_y, view_to_region)

    # Reset color
    glColor4f(0, 0, 0, 1)


def _draw_rect(x, y, width, height, view_to_region):
    glBegin(GL_LINE_LOOP)
    glVertex2f(*view_to_region(x, y, clip=False))
    glVertex2f(*view_to_region(x + width, y, clip=False))
    glVertex2f(*view_to_region(x + width, y + height, clip=False))
    glVertex2f(*view_to_region(x, y + height, clip=False))
    glEnd()


def _draw_text(text, x, y, view_to_region):
    font_id = 0
    dpi = 72
    text_size = 15
    offset = 5
    pixelpos_x, pixelpos_y = view_to_region(x, y, clip=False)

    blf.position(font_id, pixelpos_x + offset, pixelpos_y + offset, 0)
    blf.size(font_id, text_size, dpi)
    blf.draw(font_id, text)


def _denoiser_help_text(context):
    if not context.scene.luxcore.denoiser.enabled:
        return
    current_image = context.space_data.image
    if current_image is None or current_image.type != "RENDER_RESULT":
        return

    # Only show the help text if the toolshelf is not visible
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            for space in area.spaces:
                if space == context.space_data:
                    # It is the current image editor
                    for region in area.regions:
                        # Note: when the tool region is hidden, it has width == 1
                        if region.type == "TOOLS" and region.width > 1:
                            # Toolshelf is visible, do not show the help text
                            return

    image_user = context.space_data.image_user
    layer_index = image_user.multilayer_layer
    render_layers = context.scene.render.layers

    if layer_index >= len(render_layers):
        return

    render_layer = render_layers[layer_index]

    # Combined is index 0, depth is index 1 if enabled, denoised pass is right behind them
    denoised_pass_index = 2 if render_layer.luxcore.aovs.depth else 1

    if image_user.multilayer_pass == denoised_pass_index:
        # From https://github.com/sftd/blender-addons-contrib/blob/master/render_time.py
        font_id = 0  # XXX, need to find out how best to get this. [sic]
        ui_scale = context.user_preferences.view.ui_scale
        dpi = round(72 * ui_scale)

        pos_y = 45 * ui_scale
        blf.position(font_id, 15, pos_y, 0)
        blf.size(font_id, 14, dpi)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 5, 0.0, 0.0, 0.0, 1.0)

        blf.draw(font_id, '← The denoiser controls are in the "LuxCore" category')
        pos_y -= 20 * ui_scale
        blf.position(font_id, 15, pos_y, 0)
        blf.draw(font_id, 'in the tool shelf, (press T)')

        # restore defaults
        blf.disable(font_id, blf.SHADOW)
