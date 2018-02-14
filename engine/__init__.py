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
    # bl_use_shading_nodes = True  # This makes the "MATERIAL" shading mode work like in Cycles

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

            # Create a new exporter instance.
            # This is only needed when scene.render.use_persistent_data is enabled
            # because in that case our instance of LuxCoreRenderEngine is re-used
            # See https://github.com/LuxCoreRender/BlendLuxCore/issues/59
            self._exporter = export.Exporter()

            self._session = self._exporter.create_session(scene, engine=self)
        except Exception as error:
            # Will be reported in self.render() below
            self.error = error

    def render(self, scene):
        try:
            if self.error:
                # We have to re-raise the error from update() here because
                # this function (render()) is the only one that can use self.error_set()
                # to show a warning to the user after the render finished.
                raise self.error

            if self._session is None:
                # session is None, but self.error is not set -> User cancelled.
                print("Export cancelled by user.")
                return

            self.update_stats("Render", "Starting session...")
            self._framebuffer = FrameBufferFinal(scene)
            self.add_passes(scene)
            self._session.Start()

            config = self._session.GetRenderConfig()
            done = False
            start = time()

            if scene.luxcore.config.use_filesaver:
                self._session.Stop()

                if scene.luxcore.config.filesaver_format == "BIN":
                    output_path = config.GetProperties().Get("filesaver.filename").GetString()
                else:
                    output_path = config.GetProperties().Get("filesaver.directory").GetString()
                self.report({"INFO"}, 'Exported to "%s"' % output_path)

                # Clean up
                del self._session
                self._session = None
                return

            # Fast refresh on startup so the user quickly sees an image forming.
            # Not used during animation render to enhance performance.
            if not self.is_animation:
                FAST_REFRESH_DURATION = 5
                refresh_interval = utils_render.shortest_display_interval(scene)
                last_refresh = 0

                while not done:
                    now = time()

                    if now - last_refresh > refresh_interval:
                        stats = utils_render.refresh(self, scene, config, draw_film=True)
                        done = utils_render.halt_condition_met(scene, stats) or self.test_break() or self._session.HasDone()

                    if now - start > FAST_REFRESH_DURATION:
                        # It's time to switch to the loop with slow refresh below
                        break

                    # This is a measure to make cancelling more responsive in this phase
                    checks = 10
                    for i in range(checks):
                        if self.test_break():
                            done = True
                            break
                        sleep(1/60 / checks)

            # Main loop where we refresh according to user-specified interval
            last_film_refresh = time()
            stat_refresh_interval = 1
            last_stat_refresh = time()
            computed_optimal_clamp = False

            while not self.test_break() and not done:
                now = time()

                if now - last_stat_refresh > stat_refresh_interval:
                    # We have to check the stats often to see if a halt condition is met
                    # But film drawing is expensive, so we don't do it every time we check stats
                    time_until_film_refresh = scene.luxcore.display.interval - (now - last_film_refresh)
                    draw_film = time_until_film_refresh <= 0

                    # Do session update (imagepipeline, lightgroups)
                    changes = self._exporter.get_changes(scene)
                    self._exporter.update_session(changes, self._session)
                    # Refresh quickly when user changed something
                    draw_film |= changes

                    stats = utils_render.refresh(self, scene, config, draw_film, time_until_film_refresh)
                    done = utils_render.halt_condition_met(scene, stats) or self.test_break() or self._session.HasDone()

                    last_stat_refresh = now
                    if draw_film:
                        last_film_refresh = now

                # Compute and print the optimal clamp value. Done only once after a warmup phase.
                # Only do this if clamping is disabled, otherwise the value is meaningless.
                path_settings = scene.luxcore.config.path
                if not computed_optimal_clamp and not path_settings.use_clamping and time() - start > 10:
                    optimal_clamp = utils_render.find_suggested_clamp_value(self._session, scene)
                    print("Recommended clamp value:", optimal_clamp)
                    computed_optimal_clamp = True

                # Don't use up too much CPU time for this refresh loop, but stay responsive
                sleep(1 / 60)

            # User wants to stop or halt condition is reached
            # Update stats to refresh film and draw the final result
            utils_render.refresh(self, scene, config, draw_film=True)
            self.update_stats("Render", "Stopping session...")
            self._session.Stop()
            # Clean up
            del self._session
            self._session = None
        except Exception as error:
            self.report({"ERROR"}, str(error))
            self.error_set(str(error))
            import traceback
            traceback.print_exc()
            # Add error to error log so the user can inspect and copy/paste it
            scene.luxcore.errorlog.add_error(error)

            # Clean up
            del self._session
            self._session = None

    def view_update(self, context):
        # We use a custom function because sometimes we need to pass
        # some changes from view_draw() to view_update()
        self.view_update_lux(context)

    def view_update_lux(self, context, changes=None):
        print("view_update")

        if self._session is None:
            print("new session")
            try:
                self.update_stats("Creating Render Session...", "")
                # Note: in viewport render, the user can't cancel the export (Blender limitation)
                self._session = self._exporter.create_session(context.scene, context)
                self._session.Start()
                return
            except Exception as error:
                del self._session
                self._session = None
                # Reset the exporter to invalidate all caches
                self._exporter = export.Exporter()

                self.update_stats("Error: ", str(error))
                context.scene.luxcore.errorlog.add_error(error)

                import traceback
                traceback.print_exc()
                return

        if changes is None:
            changes = self._exporter.get_changes(context.scene, context)

        if changes & export.Change.CONFIG:
            # Film resize requires a new framebuffer
            self._framebuffer = FrameBuffer(context)

        # We have to re-assign the session because it might have been replaced due to filmsize change
        self._session = self._exporter.update(context, self._session, changes)

    def view_draw(self, context):
        if self._session is None:
            return

        try:
            # Check for changes because some actions in Blender (e.g. moving the viewport camera)
            # do not trigger a view_update() call, but only a view_draw() call.
            changes = self._exporter.get_changes(context.scene, context)

            if changes & export.Change.REQUIRES_VIEW_UPDATE:
                self.tag_redraw()
                self.view_update_lux(context, changes)
                return
            elif changes & export.Change.CAMERA:
                # Only update allowed in view_draw if it is a camera update, for everything else we call view_update_lux()
                # We have to re-assign the session because it might have been replaced due to filmsize change
                self._session = self._exporter.update(context, self._session, export.Change.CAMERA)

            # On startup we don't have a framebuffer yet
            if self._framebuffer is None:
                self._framebuffer = FrameBuffer(context)

            # Update and draw the framebuffer.
            self._session.UpdateStats()
            self._session.WaitNewFrame()
            self._framebuffer.update(self._session)

            region_size = context.region.width, context.region.height
            view_camera_offset = list(context.region_data.view_camera_offset)
            view_camera_zoom = context.region_data.view_camera_zoom
            self._framebuffer.draw(region_size, view_camera_offset, view_camera_zoom, self, context)

            # Check if we need to pause the viewport render
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
                # Not in pause yet, keep drawing
                self.tag_redraw()

            # Show formatted statistics in Blender UI
            config = self._session.GetRenderConfig()
            pretty_stats = utils_render.get_pretty_stats(config, stats, context.scene)
            self.update_stats(pretty_stats, status_message)
        except Exception as error:
            del self._session
            self._session = None

            self.update_stats("Error: ", str(error))
            import traceback
            traceback.print_exc()

    def add_passes(self, scene):
        """
        A custom method (not API defined) to add our custom passes.
        Called by self.render() before the render starts.
        """
        aovs = scene.luxcore.aovs

        # Note: the Depth pass is already added by Blender

        if aovs.rgb:
            self.add_pass("RGB", 3, "RGB")
        if aovs.rgba:
            self.add_pass("RGBA", 4, "RGBA")
        if aovs.alpha:
            self.add_pass("ALPHA", 1, "A")
        # if aovs.depth:
        #     self.add_pass("DEPTH", 1, "Z")
        if aovs.material_id:
            self.add_pass("MATERIAL_ID", 1, "X")
        if aovs.object_id:
            self.add_pass("OBJECT_ID", 1, "X")
        if aovs.emission:
            self.add_pass("EMISSION", 3, "RGB")
        if aovs.direct_diffuse:
            self.add_pass("DIRECT_DIFFUSE", 3, "RGB")
        if aovs.direct_glossy:
            self.add_pass("DIRECT_GLOSSY", 3, "RGB")
        if aovs.indirect_diffuse:
            self.add_pass("INDIRECT_DIFFUSE", 3, "RGB")
        if aovs.indirect_glossy:
            self.add_pass("INDIRECT_GLOSSY", 3, "RGB")
        if aovs.indirect_specular:
            self.add_pass("INDIRECT_SPECULAR", 3, "RGB")
        if aovs.position:
            self.add_pass("POSITION", 3, "XYZ")
        if aovs.shading_normal:
            self.add_pass("SHADING_NORMAL", 3, "XYZ")
        if aovs.geometry_normal:
            self.add_pass("GEOMETRY_NORMAL", 3, "XYZ")
        if aovs.uv:
            # We need to pad the UV pass to 3 elements (Blender can't handle 2 elements)
            self.add_pass("UV", 3, "UVA")
        if aovs.direct_shadow_mask:
            self.add_pass("DIRECT_SHADOW_MASK", 1, "X")
        if aovs.indirect_shadow_mask:
            self.add_pass("INDIRECT_SHADOW_MASK", 1, "X")
        if aovs.raycount:
            self.add_pass("RAYCOUNT", 1, "X")
        if aovs.samplecount:
            self.add_pass("SAMPLECOUNT", 1, "X")
        if aovs.convergence:
            self.add_pass("CONVERGENCE", 1, "X")
        if aovs.irradiance:
            self.add_pass("IRRADIANCE", 3, "RGB")

    def update_render_passes(self, scene=None, renderlayer=None):
        """
        Blender API defined method.
        Called by compositor to display sockets of custom render passes.
        """
        self.register_pass(scene, renderlayer, "Combined", 4, "RGBA", 'COLOR')

        aovs = scene.luxcore.aovs

        # Notes:
        # - The Depth pass is already added by Blender. If you add it again, it won't be displayed correctly
        #   in the "Depth" view mode of the "Combined" pass in the image editor.
        # - It seems like Blender can not handle passes with 2 elements. They must have 1, 3 or 4 elements.
        # - The last argument must be in ("COLOR", "VECTOR", "VALUE") and controls the socket color.
        if aovs.rgb:
            self.register_pass(scene, renderlayer, "RGB", 3, "RGB", "COLOR")
        if aovs.rgba:
            self.register_pass(scene, renderlayer, "RGBA", 4, "RGBA", "COLOR")
        if aovs.alpha:
            self.register_pass(scene, renderlayer, "ALPHA", 1, "A", "VALUE")
        # if aovs.depth:
        #     self.register_pass(scene, renderlayer, "DEPTH", 1, "Z", "VALUE")
        if aovs.material_id:
            self.register_pass(scene, renderlayer, "MATERIAL_ID", 1, "X", "VALUE")
        if aovs.object_id:
            self.register_pass(scene, renderlayer, "OBJECT_ID", 1, "X", "VALUE")
        if aovs.emission:
            self.register_pass(scene, renderlayer, "EMISSION", 3, "RGB", "COLOR")
        if aovs.direct_diffuse:
            self.register_pass(scene, renderlayer, "DIRECT_DIFFUSE", 3, "RGB", "COLOR")
        if aovs.direct_glossy:
            self.register_pass(scene, renderlayer, "DIRECT_GLOSSY", 3, "RGB", "COLOR")
        if aovs.indirect_diffuse:
            self.register_pass(scene, renderlayer, "INDIRECT_DIFFUSE", 3, "RGB", "COLOR")
        if aovs.indirect_glossy:
            self.register_pass(scene, renderlayer, "INDIRECT_GLOSSY", 3, "RGB", "COLOR")
        if aovs.indirect_specular:
            self.register_pass(scene, renderlayer, "INDIRECT_SPECULAR", 3, "RGB", "COLOR")
        if aovs.position:
            self.register_pass(scene, renderlayer, "POSITION", 3, "XYZ", "VECTOR")
        if aovs.shading_normal:
            self.register_pass(scene, renderlayer, "SHADING_NORMAL", 3, "XYZ", "VECTOR")
        if aovs.geometry_normal:
            self.register_pass(scene, renderlayer, "GEOMETRY_NORMAL", 3, "XYZ", "VECTOR")
        if aovs.uv:
            # We need to pad the UV pass to 3 elements (Blender can't handle 2 elements)
            self.register_pass(scene, renderlayer, "UV", 3, "UVA", "VECTOR")
        if aovs.direct_shadow_mask:
            self.register_pass(scene, renderlayer, "DIRECT_SHADOW_MASK", 1, "X", "VALUE")
        if aovs.indirect_shadow_mask:
            self.register_pass(scene, renderlayer, "INDIRECT_SHADOW_MASK", 1, "X", "VALUE")
        if aovs.raycount:
            self.register_pass(scene, renderlayer, "RAYCOUNT", 1, "X", "VALUE")
        if aovs.samplecount:
            self.register_pass(scene, renderlayer, "SAMPLECOUNT", 1, "X", "VALUE")
        if aovs.convergence:
            self.register_pass(scene, renderlayer, "CONVERGENCE", 1, "X", "VALUE")
        if aovs.irradiance:
            self.register_pass(scene, renderlayer, "IRRADIANCE", 3, "RGB", "COLOR")
