import bpy
import bgl
from .bin import pyluxcore
from .export.cache import Cache
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
        else:
            bufferdepth = 3
            self._buffertype = bgl.GL_RGB

        self.buffer = bgl.Buffer(bgl.GL_FLOAT, [width * height * bufferdepth])
        self._width = width
        self._height = height
        self._transparent = transparent

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
        self.framebuffer = None

    def __del__(self):
        # Note: this method is also called when unregister() is called (for some reason I don't understand)
        print("del")
        # TODO: stop luxcore_session here

    def update(self, data, scene):
        """Export scene data for render"""
        print("update")
        import time
        self.update_stats("Export", "exporting...")
        time.sleep(4)

    def render(self, scene):
        print("render")
        import time
        self.update_stats("Render", "rendering...")
        time.sleep(8)

    def view_update(self, context):
        print("view_update")
        print("###")

        updated_props = pyluxcore.Properties()

        for obj in context.scene.objects:
            entry = Cache.get_entry(obj)
            if entry.is_updated:
                updated_props.Set(entry.props)

            print("luxcore_names:", entry.luxcore_names)
            print("props:", entry.props)
            print("is_udpated:", entry.is_updated)
            print("---")
        print("###\n")

        # begin scene edit
        # parse updated_props
        # delete objects/lights etc.
        # end scene edit

    def view_draw(self, context):
        print("view_draw")
        # TODO: camera update, film update
        if self.framebuffer is None:
            self._init_framebuffer(context)

        # TODO: framebuffer update

        self.framebuffer.draw()

    def _init_framebuffer(self, context):
        transparent = False  # TODO
        width, height = utils.calc_filmsize(context.scene, context)
        self.framebuffer = FrameBuffer(transparent, width, height)


def register():
    print("register")

    pyluxcore.Init()
    print("pyluxcore version", pyluxcore.Version())

    from . import ui
    ui.register()
    bpy.utils.register_class(LuxCoreRenderEngine)


def unregister():
    print("unregister")
    from . import ui
    ui.unregister()
    bpy.utils.unregister_class(LuxCoreRenderEngine)
