import bpy
from time import sleep
from . import final, preview, viewport
from ..handlers.draw_imageeditor import TileStats
from ..utils.log import LuxCoreLog
from ..utils.errorlog import LuxCoreErrorLog
from ..utils import view_layer as utils_view_layer
from ..properties.display import LuxCoreDisplaySettings


class LuxCoreRenderEngine(bpy.types.RenderEngine):
    bl_idname = "LUXCORE"
    bl_label = "LuxCoreRender"

    bl_use_postprocess = True
    bl_use_preview = True
    bl_use_save_buffers = False
    bl_use_shading_nodes_custom = False
    bl_use_spherical_stereo = False
    bl_use_texture_preview = False
    bl_use_eevee_viewport = False

    final_running = False

    # Removed __init__ and __del__ methods to follow Blender API guidelines

    if bpy.app.version < (4, 4, 0):
        def __init__(self):
            self.session = None
            self.DENOISED_OUTPUT_NAME = "DENOISED"
            self.VIEWPORT_RESIZE_TIMEOUT = 0.3
            self.reset()

        def reset(self):
            self.framebuffer = None
            self.exporter = None
            self.aov_imagepipelines = {}
            self.is_first_viewport_start = True
            self.viewport_start_time = 0
            self.starting_session = False
            self.viewport_starting_message_shown = False
            self.viewport_fatal_error = None
            self.time_of_last_viewport_resize = 0
            self.last_viewport_size = (0, 0)

        def __del__(self):
            # Improved destructor to ensure proper cleanup and handle ReferenceError
            try:
                if hasattr(self, "session") and self.session:
                    if not self.is_preview:
                        print("[Engine] del: stopping session")
                    self.session.Stop()
                    del self.session
            except ReferenceError:
                print("[Engine] del: RenderEngine struct was already deleted")

        def log_listener(self, msg):
            if "Direct light sampling cache entries" in msg:
                self.update_stats("", msg)
                # Allow Blender to update the UI after the log
                sleep(0.01)

        def render(self, depsgraph):
            if self.is_preview:
                self.render_preview(depsgraph)
            else:
                self.render_final(depsgraph)

        def render_final(self, depsgraph):
            try:
                LuxCoreRenderEngine.final_running = True
                LuxCoreDisplaySettings.paused = False
                LuxCoreDisplaySettings.stop_requested = False
                TileStats.reset()
                LuxCoreLog.add_listener(self.log_listener)
                final.render(self, depsgraph)
            except Exception as error:
                error_str = str(error)
                if error_str.startswith("OpenCL device selection string has the wrong length"):
                    error_str += ". To fix this, update the OpenCL device list in the device settings"

                self.report({"ERROR"}, error_str)
                self.error_set(error_str)
                import traceback
                traceback.print_exc()
                # Add error to error log so the user can inspect and copy/paste it
                LuxCoreErrorLog.add_error(error_str)

                # Clean up safely
                self.cleanup_session()
            finally:
                utils_view_layer.State.reset()
                LuxCoreRenderEngine.final_running = False
                TileStats.reset()
                LuxCoreLog.remove_listener(self.log_listener)

        def render_preview(self, depsgraph):
            try:
                preview.render(self, depsgraph)
            except Exception as error:
                import traceback
                traceback.print_exc()
                self.cleanup_session()

        def cleanup_session(self):
            """Helper function to clean up session after errors."""
            if hasattr(self, "session"):
                del self.session
                self.session = None

        def view_update(self, context, depsgraph):
            viewport.view_update(self, context, depsgraph)

        def view_draw(self, context, depsgraph):
            try:
                viewport.view_draw(self, context, depsgraph)
            except Exception as error:
                self.cleanup_session()
                self.update_stats("Error: ", str(error))
                import traceback
                traceback.print_exc()

        def has_denoiser(self):
            return self.DENOISED_OUTPUT_NAME in self.aov_imagepipelines

        def update_render_passes(self, scene=None, renderlayer=None):
            """
            Blender API defined method.
            Called by compositor to display sockets of custom render passes.
            """
            self.register_pass(scene, renderlayer, "Combined", 4, "RGBA", 'COLOR')

            if scene.luxcore.denoiser.enabled:
                transparent = scene.camera.data.luxcore.imagepipeline.transparent_film
                self.register_denoiser_pass(scene, renderlayer, transparent)

            aovs = renderlayer.luxcore.aovs
            self.register_aov_passes(scene, renderlayer, aovs)

            # Light groups
            lightgroups = scene.luxcore.lightgroups
            lightgroup_pass_names = lightgroups.get_pass_names()
            default_group_name = lightgroups.get_lightgroup_pass_name(is_default_group=True)
            if lightgroup_pass_names != [default_group_name]:
                self.register_lightgroup_passes(scene, renderlayer, lightgroup_pass_names)

        def register_denoiser_pass(self, scene, renderlayer, transparent):
            """Helper to register the denoiser pass."""
            if transparent:
                self.register_pass(scene, renderlayer, "DENOISED", 4, "RGBA", "COLOR")
            else:
                self.register_pass(scene, renderlayer, "DENOISED", 3, "RGB", "COLOR")
    
        def register_aov_passes(self, scene, renderlayer, aovs):
            """Helper to register AOV passes."""
            if aovs.rgb:
                self.register_pass(scene, renderlayer, "RGB", 3, "RGB", "COLOR")
            if aovs.rgba:
                self.register_pass(scene, renderlayer, "RGBA", 4, "RGBA", "COLOR")
            if aovs.alpha:
                self.register_pass(scene, renderlayer, "ALPHA", 1, "A", "VALUE")
            # Add more AOV checks here (depth, albedo, etc.)

        def register_lightgroup_passes(self, scene, renderlayer, lightgroup_pass_names):
            """Helper to register lightgroup passes."""
            for name in lightgroup_pass_names:
                self.register_pass(scene, renderlayer, name, 3, "RGB", "COLOR")
                
    else:
        @classmethod
        def register(cls):
            """Register and initialize necessary attributes."""
            cls.session = None
            cls.DENOISED_OUTPUT_NAME = "DENOISED"
            cls.VIEWPORT_RESIZE_TIMEOUT = 0.3
            cls.reset()

        @classmethod
        def unregister(cls):
            """Handle cleanup and safe destruction."""
            cls.cleanup_session()
            cls.reset()

        @classmethod
        def reset(cls):
            cls.framebuffer = None
            cls.exporter = None
            cls.aov_imagepipelines = {}
            cls.is_first_viewport_start = True
            cls.viewport_start_time = 0
            cls.starting_session = False
            cls.viewport_starting_message_shown = False
            cls.viewport_fatal_error = None
            cls.time_of_last_viewport_resize = 0
            cls.last_viewport_size = (0, 0)

        @classmethod
        def cleanup_session(cls):
            """Helper function to clean up session after errors."""
            if hasattr(cls, "session") and cls.session:
                print("[Engine] del: stopping session")
                cls.session.Stop()
                del cls.session
                cls.session = None

        def log_listener(self, msg):
            if "Direct light sampling cache entries" in msg:
                self.update_stats("", msg)
                sleep(0.01)

        def render(self, depsgraph):
            if self.is_preview:
                self.render_preview(depsgraph)
            else:
                self.render_final(depsgraph)

        def render_final(self, depsgraph):
            try:
                LuxCoreRenderEngine.final_running = True
                LuxCoreDisplaySettings.paused = False
                LuxCoreDisplaySettings.stop_requested = False
                TileStats.reset()
                LuxCoreLog.add_listener(self.log_listener)
                final.render(self, depsgraph)
            except Exception as error:
                error_str = str(error)
                if error_str.startswith("OpenCL device selection string has the wrong length"):
                    error_str += ". To fix this, update the OpenCL device list in the device settings"

                self.report({"ERROR"}, error_str)
                self.error_set(error_str)
                import traceback
                traceback.print_exc()
                LuxCoreErrorLog.add_error(error_str)

                # Clean up safely
                self.cleanup_session()
            finally:
                utils_view_layer.State.reset()
                LuxCoreRenderEngine.final_running = False
                TileStats.reset()
                LuxCoreLog.remove_listener(self.log_listener)

        def render_preview(self, depsgraph):
            try:
                preview.render(self, depsgraph)
            except Exception as error:
                import traceback
                traceback.print_exc()
                self.cleanup_session()

        def view_update(self, context, depsgraph):
            viewport.view_update(self, context, depsgraph)

        def view_draw(self, context, depsgraph):
            try:
                viewport.view_draw(self, context, depsgraph)
            except Exception as error:
                self.cleanup_session()
                self.update_stats("Error: ", str(error))
                import traceback
                traceback.print_exc()

        def has_denoiser(self):
            return self.DENOISED_OUTPUT_NAME in self.aov_imagepipelines

        def update_render_passes(self, scene=None, renderlayer=None):
            self.register_pass(scene, renderlayer, "Combined", 4, "RGBA", 'COLOR')

            if scene.luxcore.denoiser.enabled:
                transparent = scene.camera.data.luxcore.imagepipeline.transparent_film
                self.register_denoiser_pass(scene, renderlayer, transparent)

            aovs = renderlayer.luxcore.aovs
            self.register_aov_passes(scene, renderlayer, aovs)

            lightgroups = scene.luxcore.lightgroups
            lightgroup_pass_names = lightgroups.get_pass_names()
            default_group_name = lightgroups.get_lightgroup_pass_name(is_default_group=True)
            if lightgroup_pass_names != [default_group_name]:
                self.register_lightgroup_passes(scene, renderlayer, lightgroup_pass_names)

        def register_denoiser_pass(self, scene, renderlayer, transparent):
            if transparent:
                self.register_pass(scene, renderlayer, "DENOISED", 4, "RGBA", "COLOR")
            else:
                self.register_pass(scene, renderlayer, "DENOISED", 3, "RGB", "COLOR")

        def register_aov_passes(self, scene, renderlayer, aovs):
            if aovs.rgb:
                self.register_pass(scene, renderlayer, "RGB", 3, "RGB", "COLOR")
            if aovs.rgba:
                self.register_pass(scene, renderlayer, "RGBA", 4, "RGBA", "COLOR")
            if aovs.alpha:
                self.register_pass(scene, renderlayer, "ALPHA", 1, "A", "VALUE")

        def register_lightgroup_passes(self, scene, renderlayer, lightgroup_pass_names):
            for name in lightgroup_pass_names:
                self.register_pass(scene, renderlayer, name, 3, "RGB", "COLOR")
