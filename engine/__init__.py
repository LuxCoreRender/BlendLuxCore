import bpy
from time import sleep
from . import final, preview, viewport
from ..handlers.draw_imageeditor import TileStats
from ..utils.log import LuxCoreLog


class LuxCoreRenderEngine(bpy.types.RenderEngine):
    bl_idname = "LUXCORE"
    bl_label = "LuxCore"

    # When rendering an animation, this prevents layers from being updated if they
    # are excluded on all render layers.
    bl_use_exclude_layers = True

    # No idea what this flag does exactly.
    bl_use_postprocess = True

    # Enables material preview (but not texture preview) for this render engine.
    # Previews call self.render() like a final render. We have to check self.is_preview
    # to see if we should render a preview.
    bl_use_preview = True

    # Has something to do with tiled EXR render output, not sure about the details.
    bl_use_save_buffers = False

    # This makes the "MATERIAL" shading mode work like in Cycles. Currently we can't
    # use this, it requires GLSL code for each node, which has to be defined in C.
    bl_use_shading_nodes = False

    # Hides Cycles node trees in the node editor.
    bl_use_shading_nodes_custom = True

    # Sets the value of the property scene.render.use_spherical_stereo
    # (this is all it does as far as I could see in the Blender source code).
    bl_use_spherical_stereo = False

    # Texture previews are disabled intentionally. It is faster and easier to let
    # Blender Internal render them. They are only shown for brush textures,
    # displacement textures etc., not for LuxCore textures.
    bl_use_texture_preview = False

    final_running = False

    def __init__(self):
        self.session = None
        self.DENOISED_OUTPUT_NAME = "DENOISED"
        self.reset()

    def reset(self):
        self.framebuffer = None
        self.exporter = None
        self.error = None
        self.aov_imagepipelines = {}
        self.viewport_start_time = 0

    def __del__(self):
        # Note: this method is also called when unregister() is called (for some reason I don't understand)
        if getattr(self, "session", None):
            if not self.is_preview:
                print("[Engine] del: stopping session")
            self.session.Stop()
            del self.session

    def log_listener(self, msg):
        if "Direct light sampling cache entries" in msg:
            self.update_stats("", msg)
            # We have to sleep for a bit, otherwise Blender does not update the UI
            sleep(0.01)
        # elif "BCD progress" in msg:  # TODO For some weird reason this does not work
        #     self.update_stats("", msg)

    def render(self, scene):
        if self.is_preview:
            self.render_preview(scene)
        else:
            self.render_final(scene)

    def render_final(self, scene):
        try:
            LuxCoreRenderEngine.final_running = True
            scene.luxcore.display.paused = False
            TileStats.reset()
            LuxCoreLog.add_listener(self.log_listener)
            final.render(self, scene)
        except Exception as error:
            self.report({"ERROR"}, str(error))
            self.error_set(str(error))
            import traceback
            traceback.print_exc()
            # Add error to error log so the user can inspect and copy/paste it
            scene.luxcore.errorlog.add_error(error)

            # Clean up
            del self.session
            self.session = None
        finally:
            scene.luxcore.active_layer_index = -1
            LuxCoreRenderEngine.final_running = False
            TileStats.reset()
            LuxCoreLog.remove_listener(self.log_listener)

    def render_preview(self, scene):
        try:
            preview.render(self, scene)
        except Exception as error:
            import traceback
            traceback.print_exc()
            # Clean up
            del self.session
            self.session = None

    def view_update(self, context):
        viewport.view_update(self, context)

    def view_draw(self, context):
        if self.session is None:
            return

        try:
            viewport.view_draw(self, context)
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
