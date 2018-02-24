import bpy
from .. import export
from . import final, viewport


class LuxCoreRenderEngine(bpy.types.RenderEngine):
    bl_idname = "LUXCORE"
    bl_label = "LuxCore"
    bl_use_preview = False  # TODO: disabled for now
    bl_use_shading_nodes_custom = True
    # bl_use_shading_nodes = True  # This makes the "MATERIAL" shading mode work like in Cycles

    def __init__(self):
        print("init")
        self.framebuffer = None
        self.session = None
        self.exporter = export.Exporter()
        self.error = None

    def __del__(self):
        # Note: this method is also called when unregister() is called (for some reason I don't understand)
        print("LuxCoreRenderEngine del")
        if hasattr(self, "_session") and self.session:
            print("del: stopping session")
            self.session.Stop()
            del self.session

    def update(self, data, scene):
        """Export scene data for render"""
        try:
            final.update(self, scene)
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

    def add_passes(self, scene):
        """
        A custom method (not API defined) to add our custom passes.
        Called by self.render() before the render starts.
        """
        aovs = scene.luxcore.aovs

        # Note: The Depth pass is already added by Blender. If we add it again, it won't be
        # displayed correctly in the "Depth" view mode of the "Combined" pass in the image editor.

        if aovs.rgb:
            self.add_pass("RGB", 3, "RGB")
        if aovs.rgba:
            self.add_pass("RGBA", 4, "RGBA")
        if aovs.alpha:
            self.add_pass("ALPHA", 1, "A")
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
