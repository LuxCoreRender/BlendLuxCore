import bpy
from time import time, sleep
from ..bin import pyluxcore
from ..draw import FrameBuffer, FrameBufferFinal
from .. import export


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
        self.error = None

    def __del__(self):
        # Note: this method is also called when unregister() is called (for some reason I don't understand)
        print("LuxCoreRenderEngine del")
        if hasattr(self, "_session") and self._session:
            print("del: stopping session")
            self._session.Stop()
            del self._session

    def update(self, data, scene):
        """Export scene data for render"""
        try:
            assert self._session is None
            self.update_stats("Export", "exporting...")

            self._session = self._exporter.create_session(scene)
        except Exception as error:
            # Will be reported in self.render() below
            self.error = error

    def render(self, scene):
        try:
            if self.error:
                raise self.error

            assert self._session is not None
            self.update_stats("Render", "rendering...")
            self._framebuffer = FrameBufferFinal(scene)
            self._session.Start()
            self._framebuffer.draw(self, self._session)

            last_refresh = time()
            interval = 3
            while not self.test_break():
                sleep(1 / 50)
                now = time()
                if now - last_refresh > interval:
                    self._session.UpdateStats()
                    self._framebuffer.draw(self, self._session)
                    last_refresh = now

            self._session.Stop()
            self._framebuffer.draw(self, self._session)
        except Exception as error:
            self.report({'ERROR'}, str(error))
            import traceback
            traceback.print_exc()
            scene.luxcore.errorlog.set(error)

    def view_update(self, context):
        self.view_update_lux(context)

    def view_update_lux(self, context, changes=None):
        print("view_update")

        if self._session is None:
            self._session = self._exporter.create_session(context.scene, context)
            self._session.Start()
            return

        if changes is None:
            changes = self._exporter.get_changes(context)
        self._exporter.update(context, self._session, changes)

    def view_draw(self, context):
        # TODO: film resize update

        changes = self._exporter.get_changes(context)

        if changes & export.Change.REQUIRES_VIEW_UPDATE:
            if changes & export.Change.CONFIG:
                # Film resize requires a new framebuffer
                self._framebuffer = FrameBuffer(context)
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