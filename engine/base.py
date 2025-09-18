from time import sleep
_needs_reload = "bpy" in locals()

import bpy
import pyluxcore
from . import final, preview, viewport
from .. import handlers, utils, properties
from ..handlers.draw_imageeditor import TileStats
from ..utils.log import LuxCoreLog
from ..utils.errorlog import LuxCoreErrorLog
from ..utils import view_layer as utils_view_layer
from ..utils import get_addon_preferences
from ..properties.display import LuxCoreDisplaySettings


if _needs_reload:
    import importlib

    modules = (final, preview, viewport, handlers, utils, properties)
    for module in modules:
        importlib.reload(module)


class LuxCoreRenderEngine(bpy.types.RenderEngine):
    bl_idname = "LUXCORE"
    bl_label = "LuxCoreRender"

    # Apply compositing on render results.
    bl_use_postprocess = True

    # Enables material preview (but not texture preview) for this render engine.
    # Previews call self.render() like a final render. We have to check self.is_preview
    # to see if we should render a preview.
    bl_use_preview = True

    # Has something to do with tiled EXR render output, not sure about the details.
    bl_use_save_buffers = False

    # Hides Cycles node trees in the node editor.
    bl_use_shading_nodes_custom = False

    # Sets the value of the property scene.render.use_spherical_stereo
    # (this is all it does as far as I could see in the Blender source code).
    bl_use_spherical_stereo = False

    # Texture previews are disabled intentionally. It is faster and easier to let
    # Blender Internal render them. They are only shown for brush textures,
    # displacement textures etc., not for LuxCore textures.
    bl_use_texture_preview = False

    # Use Eevee nodes in look dev ("MATERIAL") shading mode in the viewport.
    bl_use_eevee_viewport = False

    final_running = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        # Note: this method is also called when unregister() is called (for some reason I don't understand)
        try:
            if getattr(self, "session", None):
                if not self.is_preview:
                    print("[Engine] del: stopping session")
                self.session.Stop()
                del self.session
        except ReferenceError:
            print("[Engine] del: RenderEngine struct was already deleted")

    def log_listener(self, msg):
        if "Direct light sampling cache entries" in msg:
            self.update_stats("", msg)
            # We have to sleep for a bit, otherwise Blender does not update the UI
            sleep(0.01)

    def render(self, depsgraph):
        display_luxcore_logs = get_addon_preferences(bpy.context).display_luxcore_logs
        if display_luxcore_logs:
            pyluxcore.SetLogHandler(LuxCoreLog.add)
        else:
            pyluxcore.SetLogHandler(LuxCoreLog.silent)
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

            # Clean up
            del self.session
            self.session = None
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
            # Clean up
            del self.session
            self.session = None

    def view_update(self, context, depsgraph):
        viewport.view_update(self, context, depsgraph)

    def view_draw(self, context, depsgraph):
        try:
            viewport.view_draw(self, context, depsgraph)
        except Exception as error:
            del self.session
            self.session = None

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

        # Denoiser
        if scene.luxcore.denoiser.enabled:
            transparent = scene.camera.data.luxcore.imagepipeline.transparent_film
            if transparent:
                self.register_pass(scene, renderlayer, "DENOISED", 4, "RGBA", "COLOR")
            else:
                self.register_pass(scene, renderlayer, "DENOISED", 3, "RGB", "COLOR")

        aovs = renderlayer.luxcore.aovs

        # Notes:
        # - It seems like Blender can not handle passes with 2 elements. They must have 1, 3 or 4 elements.
        # - The last argument must be in ("COLOR", "VECTOR", "VALUE") and controls the socket color.
        if aovs.rgb:
            self.register_pass(scene, renderlayer, "RGB", 3, "RGB", "COLOR")
        if aovs.rgba:
            self.register_pass(scene, renderlayer, "RGBA", 4, "RGBA", "COLOR")
        if aovs.alpha:
            self.register_pass(scene, renderlayer, "ALPHA", 1, "A", "VALUE")
        if aovs.depth:
            # In the compositor we need to register the Depth pass
            self.register_pass(scene, renderlayer, "Depth", 1, "Z", "VALUE")
        if aovs.albedo:
            self.register_pass(scene, renderlayer, "ALBEDO", 3, "RGB", "COLOR")
        if aovs.material_id:
            self.register_pass(scene, renderlayer, "MATERIAL_ID", 1, "X", "VALUE")
        if aovs.material_id_color:
            self.register_pass(scene, renderlayer, "MATERIAL_ID_COLOR", 3, "RGB", "COLOR")
        if aovs.object_id:
            self.register_pass(scene, renderlayer, "OBJECT_ID", 1, "X", "VALUE")
        if aovs.emission:
            self.register_pass(scene, renderlayer, "EMISSION", 3, "RGB", "COLOR")
        if aovs.caustic:
            self.register_pass(scene, renderlayer, "CAUSTIC", 3, "RGB", "COLOR")
        if aovs.direct_diffuse:
            self.register_pass(scene, renderlayer, "DIRECT_DIFFUSE", 3, "RGB", "COLOR")
        if aovs.direct_diffuse_reflect:
            self.register_pass(scene, renderlayer, "DIRECT_DIFFUSE_REFLECT", 3, "RGB", "COLOR")
        if aovs.direct_diffuse_transmit:
            self.register_pass(scene, renderlayer, "DIRECT_DIFFUSE_TRANSMIT", 3, "RGB", "COLOR")
        if aovs.direct_glossy:
            self.register_pass(scene, renderlayer, "DIRECT_GLOSSY", 3, "RGB", "COLOR")
        if aovs.direct_glossy_reflect:
            self.register_pass(scene, renderlayer, "DIRECT_GLOSSY_REFLECT", 3, "RGB", "COLOR")
        if aovs.direct_glossy_transmit:
            self.register_pass(scene, renderlayer, "DIRECT_GLOSSY_TRANSMIT", 3, "RGB", "COLOR")
        if aovs.indirect_diffuse:
            self.register_pass(scene, renderlayer, "INDIRECT_DIFFUSE", 3, "RGB", "COLOR")
        if aovs.indirect_diffuse_reflect:
            self.register_pass(scene, renderlayer, "INDIRECT_DIFFUSE_REFLECT", 3, "RGB", "COLOR")
        if aovs.indirect_diffuse_transmit:
            self.register_pass(scene, renderlayer, "INDIRECT_DIFFUSE_TRANSMIT", 3, "RGB", "COLOR")
        if aovs.indirect_glossy:
            self.register_pass(scene, renderlayer, "INDIRECT_GLOSSY", 3, "RGB", "COLOR")
        if aovs.indirect_glossy_reflect:
            self.register_pass(scene, renderlayer, "INDIRECT_GLOSSY_REFLECT", 3, "RGB", "COLOR")
        if aovs.indirect_glossy_transmit:
            self.register_pass(scene, renderlayer, "INDIRECT_GLOSSY_TRANSMIT", 3, "RGB", "COLOR")
        if aovs.indirect_specular:
            self.register_pass(scene, renderlayer, "INDIRECT_SPECULAR", 3, "RGB", "COLOR")
        if aovs.indirect_specular_reflect:
            self.register_pass(scene, renderlayer, "INDIRECT_SPECULAR_REFLECT", 3, "RGB", "COLOR")
        if aovs.indirect_specular_transmit:
            self.register_pass(scene, renderlayer, "INDIRECT_SPECULAR_TRANSMIT", 3, "RGB", "COLOR")
        if aovs.position:
            self.register_pass(scene, renderlayer, "POSITION", 3, "XYZ", "VECTOR")
        if aovs.shading_normal:
            self.register_pass(scene, renderlayer, "SHADING_NORMAL", 3, "XYZ", "VECTOR")
        if aovs.avg_shading_normal:
            self.register_pass(scene, renderlayer, "AVG_SHADING_NORMAL", 3, "XYZ", "VECTOR")
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
        if aovs.noise:
            self.register_pass(scene, renderlayer, "NOISE", 1, "X", "VALUE")
        if aovs.irradiance:
            self.register_pass(scene, renderlayer, "IRRADIANCE", 3, "RGB", "COLOR")

        # Light groups
        lightgroups = scene.luxcore.lightgroups
        lightgroup_pass_names = lightgroups.get_pass_names()
        default_group_name = lightgroups.get_lightgroup_pass_name(is_default_group=True)
        # If only the default group is in the list, it doesn't make sense to show lightgroups
        # Note: this behaviour has to be the same as in the _add_passes() function in the engine/final.py file
        if lightgroup_pass_names != [default_group_name]:
            for name in lightgroup_pass_names:
                self.register_pass(scene, renderlayer, name, 3, "RGB", "COLOR")
