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
    def __init__(self, transparent, width, height):
        if transparent:
            bufferdepth = 4
            self._buffertype = bgl.GL_RGBA
            self._output_type = pyluxcore.FilmOutputType.RGBA_IMAGEPIPELINE
        else:
            bufferdepth = 3
            self._buffertype = bgl.GL_RGB
            self._output_type = pyluxcore.FilmOutputType.RGB_IMAGEPIPELINE

        self.buffer = bgl.Buffer(bgl.GL_FLOAT, [width * height * bufferdepth])
        self._width = width
        self._height = height
        self._transparent = transparent

    def update(self, luxcore_session):
        luxcore_session.GetFilm().GetOutputFloat(self._output_type, self.buffer)

    def draw(self):
        if self._transparent:
            bgl.glEnable(bgl.GL_BLEND)

        bgl.glRasterPos2i(0, 0)
        bgl.glDrawPixels(self._width, self._height, self._buffertype, bgl.GL_FLOAT, self.buffer)

        if self._transparent:
            bgl.glDisable(bgl.GL_BLEND)


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

        self._framebuffer.draw()
        self.tag_redraw()

    def _init_framebuffer(self, context):
        # TODO: maybe move all of this to FrameBuffer constructor
        transparent = False  # TODO
        width, height = utils.calc_filmsize(context.scene, context)
        self._framebuffer = FrameBuffer(transparent, width, height)


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
