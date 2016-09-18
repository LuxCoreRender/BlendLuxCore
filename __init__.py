import bpy
import bgl
from .bin import pyluxcore
from .export.cache import Cache
from .export import config, camera
from . import export
from . import utils

bl_info = {
    "name": "LuxCore",
    "author": "Simon Wendsche (B.Y.O.B.)",
    "version": (1, 7),
    "blender": (2, 77, 0),
    "category": "Render",
    "location": "Info header, render engine menu",
    "description": "LuxCore integration for Blender",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}


class FrameBuffer(object):
    def __init__(self, transparent, filmsize, border):
        self._width = filmsize[0]
        self._height = filmsize[1]
        self._border = border

        if transparent:
            bufferdepth = 4
            self._buffertype = bgl.GL_RGBA
            self._output_type = pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
        else:
            bufferdepth = 3
            self._buffertype = bgl.GL_RGB
            self._output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE

        self.buffer = bgl.Buffer(bgl.GL_FLOAT, [self._width * self._height * bufferdepth])
        self._transparent = transparent

    def update(self, luxcore_session):
        luxcore_session.GetFilm().GetOutputFloat(self._output_type, self.buffer)

    def draw(self, region_size, view_camera_offset):
        if self._transparent:
            bgl.glEnable(bgl.GL_BLEND)

        offset_x, offset_y = self._calc_offset(region_size, view_camera_offset)

        bgl.glRasterPos2i(offset_x, offset_y)
        bgl.glDrawPixels(self._width, self._height, self._buffertype, bgl.GL_FLOAT, self.buffer)

        if self._transparent:
            bgl.glDisable(bgl.GL_BLEND)

    def _calc_offset(self, region_size, view_camera_offset):
        # TODO: view_camera_offset, to get correct draw position in camera viewport mode
        width_raw, height_raw = region_size
        border_min_x, border_max_x, border_min_y, border_max_y = self._border

        # TODO: not sure about the +1, needs further testing to see if rounding is better
        offset_x = width_raw * border_min_x + 1
        offset_y = height_raw * border_min_y + 1

        #view_camera_offset = [(v + 1) / 2 for v in view_camera_offset]
        # view_cam_shift_x = width_raw * view_camera_offset[0]
        # view_cam_shift_y = height_raw * view_camera_offset[1]

        # xaspect, yaspect = utils.calc_aspect(width_raw, height_raw)
        # offset_x = (view_camera_offset[0] * xaspect * 2) * width_raw
        # offset_y = (view_camera_offset[1] * yaspect * 2) * height_raw
        #print("offsets:", offset_x, offset_y)


        # view_camera_offset is completely weird (range -1..1, mirrored axis),
        # bring it into 0..1 range with 0,0 in lower left corner and 1,1 in upper right corner
        # view_camera_offset[0] = 1 - (view_camera_offset[0] + 1) / 2
        # view_camera_offset[1] = 1 - (view_camera_offset[1] + 1) / 2
        # offset_x = view_camera_offset[0] * width_raw
        # offset_y = view_camera_offset[1] * height_raw
        # print("offsets:", offset_x, offset_y)


        # offset_x, offset_y are in pixels
        return int(offset_x), int(offset_y)


class LuxCoreRenderEngine(bpy.types.RenderEngine):
    bl_idname = "LUXCORE"
    bl_label = "LuxCore"
    bl_use_preview = False  # TODO: disabled for now
    bl_use_shading_nodes_custom = True

    def __init__(self):
        print("init")
        self._framebuffer = None
        self._session = None
        self._exporter = export.Exporter()

    def __del__(self):
        # Note: this method is also called when unregister() is called (for some reason I don't understand)
        print("del")
        if hasattr(self, "_session") and self._session:
            print("del: stopping session")
            self._session.Stop()
            del self._session

    def update(self, data, scene):
        """Export scene data for render"""
        print("update")
        import time
        self.update_stats("Export", "exporting...")
        time.sleep(1)

    def render(self, scene):
        print("render")
        import time
        self.update_stats("Render", "rendering...")
        time.sleep(2)

    def view_update(self, context):
        print("view_update")

        if self._session is None:
            self._session = self._exporter.create_session(context.scene, context)
            self._session.Start()
            return

        self._exporter.needs_update(context)
        self._exporter.execute_update(context, self._session)

    def view_draw(self, context):
        #print("view_draw")
        # TODO: camera update, film update
        self._exporter.needs_draw_update(context)
        self._exporter.execute_update(context, self._session)

        if self._framebuffer is None:
            self._init_framebuffer(context)

        if self._session:
            self._session.UpdateStats()
            self._session.WaitNewFrame()
            self._framebuffer.update(self._session)

        region_size = context.region.width, context.region.height
        view_camera_offset = list(context.region_data.view_camera_offset)
        self._framebuffer.draw(region_size, view_camera_offset)
        self.tag_redraw()

    def _init_framebuffer(self, context):
        # TODO: maybe move all of this to FrameBuffer constructor
        transparent = False  # TODO
        filmsize = utils.calc_filmsize(context.scene, context)
        border = utils.calc_blender_border(context.scene, context)
        self._framebuffer = FrameBuffer(transparent, filmsize, border)


def register():
    print("register BlendLuxCore")

    pyluxcore.Init()
    print("pyluxcore version", pyluxcore.Version())

    from . import ui
    ui.register()
    bpy.utils.register_class(LuxCoreRenderEngine)


def unregister():
    print("unregister BlendLuxCore")
    from . import ui
    ui.unregister()
    bpy.utils.unregister_class(LuxCoreRenderEngine)
