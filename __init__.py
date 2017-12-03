import bpy
from .bin import pyluxcore
from .draw import FrameBuffer
from . import export

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
        print("LuxCoreRenderEngine del")
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
        self.view_update_lux(context)

    def view_update_lux(self, context, changes=None):
        print("view_update")

        if self._session is None:
            self._session = self._exporter.create_session(context.scene, context)
            self._session.Start()
            return

        # new
        if changes is None:
            changes = self._exporter.get_changes(context)
        self._exporter.update(context, self._session, changes)

    def view_draw(self, context):
        # TODO: film resize update

        changes = self._exporter.get_changes(context)

        if changes & export.Change.REQUIRES_VIEW_UPDATE:
            self.view_update_lux(context, changes)
            return
        elif changes & export.Change.CAMERA:
            # Only update allowed in view_draw is a camera update, for everything else we call view_update_lux()
            self._exporter.update(context, self._session, export.Change.CAMERA)

        if self._framebuffer is None:
            self._framebuffer = FrameBuffer(context)

        if self._session:
            self._session.UpdateStats()
            self._session.WaitNewFrame()
            self._framebuffer.update(self._session)

        region_size = context.region.width, context.region.height
        view_camera_offset = list(context.region_data.view_camera_offset)
        self._framebuffer.draw(region_size, view_camera_offset)
        self.tag_redraw()


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
