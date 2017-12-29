import bpy
from time import time, sleep
from ..bin import pyluxcore
from ..draw import FrameBuffer, FrameBufferFinal
from .. import export
from ..utils import render as utils_render


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
        # Note: this method is also called when unregister() is called (for some reason I don"t understand)
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
            # Clear error log
            scene.luxcore.errorlog.set("")

            if self.error:
                raise self.error

            assert self._session is not None
            self.update_stats("Render", "Starting...")
            self._framebuffer = FrameBufferFinal(scene)
            self._session.Start()
            self._framebuffer.draw(self, self._session)

            config = self._session.GetRenderConfig()

            # Fast refresh on startup so the user quickly sees an image forming.
            # Not used during animation render to enhance performance.
            if not self.is_animation:
                FAST_REFRESH_DURATION = 5
                refresh_interval = utils_render.shortest_display_interval(scene)
                last_refresh = 0
                done = False
                start = time()

                while not self.test_break() and not done:
                    # Don't use up too much CPU time
                    sleep(1 / 60)
                    now = time()

                    if now - last_refresh > refresh_interval:
                        stats = utils_render.refresh(self, scene, config, draw_film=True)
                        done = utils_render.halt_condition_met(scene, stats)

                    if now - start > FAST_REFRESH_DURATION:
                        # It's time to switch to the loop with slow refresh below
                        break

            # Main loop where we refresh according to user-specified interval
            last_film_refresh = time()
            stat_refresh_interval = 1
            last_stat_refresh = time()
            done = False

            while not self.test_break() and not done:
                # Don't use up too much CPU time
                sleep(1 / 60)
                now = time()

                if now - last_stat_refresh > stat_refresh_interval:
                    # We have to check the stats often to see if a halt condition is met
                    # But film drawing is expensive, so we don't do it every time we check stats
                    time_until_film_refresh = scene.luxcore.display.interval - (now - last_film_refresh)
                    draw_film = time_until_film_refresh <= 0

                    stats = utils_render.refresh(self, scene, config, draw_film, time_until_film_refresh)
                    done = utils_render.halt_condition_met(scene, stats)

                    last_stat_refresh = now
                    if draw_film:
                        last_film_refresh = now

            self._session.Stop()
            self._framebuffer.draw(self, self._session)
            del self._session
            self._session = None
        except Exception as error:
            del self._session
            self._session = None

            self.report({"ERROR"}, str(error))
            self.error_set(str(error))
            import traceback
            traceback.print_exc()
            scene.luxcore.errorlog.set(error)

    def view_update(self, context):
        self.view_update_lux(context)

    def view_update_lux(self, context, changes=None):
        print("view_update")

        if self._session is None:
            print("new session")
            try:
                self.update_stats("Creating Render Session...", "")
                self._session = self._exporter.create_session(context.scene, context)
                self._session.Start()
                return
            except Exception as error:
                del self._session
                self._session = None

                self.update_stats("Error: ", str(error))
                import traceback
                traceback.print_exc()
                return

        if changes is None:
            changes = self._exporter.get_changes(context)
        # We have to re-assign the session because it might have been replaced due to filmsize change
        self._session = self._exporter.update(context, self._session, changes)

    def view_draw(self, context):
        if self._session is None:
            return

        try:
            changes = self._exporter.get_changes(context)

            if changes & export.Change.REQUIRES_VIEW_UPDATE:
                if changes & export.Change.CONFIG:
                    # Film resize requires a new framebuffer
                    self._framebuffer = FrameBuffer(context)
                self.tag_redraw()
                self.view_update_lux(context, changes)
                return
            elif changes & export.Change.CAMERA:
                # Only update allowed in view_draw if it is a camera update, for everything else we call view_update_lux()
                # We have to re-assign the session because it might have been replaced due to filmsize change
                self._session = self._exporter.update(context, self._session, export.Change.CAMERA)

            if self._framebuffer is None:
                self._framebuffer = FrameBuffer(context)

            self._session.UpdateStats()
            self._session.WaitNewFrame()
            self._framebuffer.update(self._session)

            region_size = context.region.width, context.region.height
            view_camera_offset = list(context.region_data.view_camera_offset)
            view_camera_zoom = context.region_data.view_camera_zoom
            
            self._framebuffer.draw(region_size, view_camera_offset, view_camera_zoom, self, context)

            stats = self._session.GetStats()
            rendered_time = stats.Get("stats.renderengine.time").GetFloat()
            halt_time = context.scene.luxcore.display.viewport_halt_time
            status_message = "%d/%ds" % (rendered_time, halt_time)
            if rendered_time > halt_time:
                if not self._session.IsInPause():
                    print("Pausing session")
                    self._session.Pause()
                status_message += " (Paused)"
            else:
                self.tag_redraw()

            config = self._session.GetRenderConfig()
            pretty_stats = utils_render.get_pretty_stats(config, stats, context.scene.luxcore.halt)
            self.update_stats(pretty_stats, status_message)
        except Exception as error:
            del self._session
            self._session = None

            self.update_stats("Error: ", str(error))
            import traceback
            traceback.print_exc()
