import bpy
import blf
from bgl import *
import gpu
from gpu_extras.batch import batch_for_shader

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
#    _denoiser_help_text(context)


def _tile_highlight(context):
    current_image = context.space_data.image
    if current_image is None or current_image.type != "RENDER_RESULT":
        return
    from ..engine.base import LuxCoreRenderEngine
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
    if not coords or TileStats.film_width == 0 or TileStats.film_height == 0:
        return

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

        _draw_rect(rel_x, rel_y, rel_width, rel_height, color, view_to_region)

        if passcounts:
            _draw_text(str(passcounts[i]), rel_x, rel_y, color, view_to_region)

def _draw_rect(x, y, width, height, color, view_to_region):
    x1, y1 = view_to_region(x, y, clip=False)
    x2, y2 = view_to_region(x + width, y, clip=False)
    x3, y3 = view_to_region(x + width, y + height, clip=False)
    x4, y4 = view_to_region(x, y + height, clip=False)

    co = ((x1, y1), (x2, y2), (x3, y3), (x4, y4))
    indices = ((0, 1), (1, 2), (2, 3), (3, 0))

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": co}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _draw_text(text, x, y, color, view_to_region):
    font_id = 0
    dpi = 72
    text_size = 12
    offset = 5
    pixelpos_x, pixelpos_y = view_to_region(x, y, clip=False)

    r, g, b, a = color
    blf.position(font_id, pixelpos_x + offset, pixelpos_y + offset, 0)
    blf.color(font_id, r,g,b,a)
    blf.size(font_id, text_size)
    blf.draw(font_id, text)
