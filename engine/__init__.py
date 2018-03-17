import bpy
from . import final, preview, viewport


class LuxCoreRenderEngine(bpy.types.RenderEngine):
    bl_idname = "LUXCORE"
    bl_label = "LuxCore"
    bl_use_preview = True
    bl_use_shading_nodes_custom = True
    # bl_use_shading_nodes = True  # This makes the "MATERIAL" shading mode work like in Cycles
    bl_use_exclude_layers = True  # No idea what this does, but we support exclude layers
    bl_use_postprocess = True  # No idea what this does

    def __init__(self):
        print("init")
        self.framebuffer = None
        self.session = None
        self.exporter = None
        self.error = None
        self.aov_imagepipelines = {}

    def __del__(self):
        # Note: this method is also called when unregister() is called (for some reason I don't understand)
        print("LuxCoreRenderEngine del")
        if hasattr(self, "_session") and self.session:
            print("del: stopping session")
            self.session.Stop()
            del self.session

    def render(self, scene):
        if self.is_preview:
            self.render_preview(scene)
        else:
            self.render_final(scene)

    def render_final(self, scene):
        try:
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

    def update_render_passes(self, scene=None, renderlayer=None):
        """
        Blender API defined method.
        Called by compositor to display sockets of custom render passes.
        """
        self.register_pass(scene, renderlayer, "Combined", 4, "RGBA", 'COLOR')

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
