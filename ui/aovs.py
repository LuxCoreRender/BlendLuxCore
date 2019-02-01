from bl_ui.properties_render_layer import RenderLayerButtonsPanel
from bpy.types import Panel
from ..ui import icons

COMPATIBLE_WITH_BIDIR = {
    "RADIANCE_GROUP", "SAMPLECOUNT",
    "ALPHA", "RGBA", "RGB", "DEPTH"
}


class LUXCORE_RENDERLAYER_PT_aovs(RenderLayerButtonsPanel, Panel):
    bl_label = "LuxCore Arbitrary Output Variables (AOVs)"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        active_layer = context.scene.render.layers.active
        aovs = active_layer.luxcore.aovs
        engine_is_path = context.scene.luxcore.config.engine == "PATH"

        if not engine_is_path:
            layout.label("The Bidir engine only supports a few AOVs", icon=icons.INFO)

        split = layout.split()
        col = split.column(align=True)

        col.label("Basic Information")
        col.prop(aovs, "rgb")
        col.prop(aovs, "rgba")
        col.prop(aovs, "alpha")
        col.prop(aovs, "depth")
        col.prop(aovs, "albedo")

        # All following AOVs are not supported by BIDIR, only by PATH
        sub = col.column(align=True)
        sub.active = engine_is_path
        sub.label("Material/Object Information")
        sub.prop(aovs, "material_id")
        sub.prop(aovs, "material_id_color")
        sub.prop(aovs, "object_id")
        sub.prop(aovs, "emission")

        sub.label("Direct Light Information")
        sub.prop(aovs, "direct_diffuse")
        sub.prop(aovs, "direct_glossy")

        sub.label("Indirect Light Information")
        sub.prop(aovs, "indirect_diffuse")
        sub.prop(aovs, "indirect_glossy")
        sub.prop(aovs, "indirect_specular")

        col = split.column(align=True)

        sub = col.column(align=True)
        sub.active = engine_is_path

        sub.label("Geometry Information")
        sub.prop(aovs, "position")
        sub.prop(aovs, "shading_normal")
        sub.prop(aovs, "geometry_normal")
        sub.prop(aovs, "uv")

        sub.label("Shadow Information")
        sub.prop(aovs, "direct_shadow_mask")
        sub.prop(aovs, "indirect_shadow_mask")

        sub.label("Render Information")
        sub.prop(aovs, "irradiance")
        sub.prop(aovs, "raycount")
        sub.prop(aovs, "convergence")

        # Samplecount is supported by BIDIR again
        col.prop(aovs, "samplecount")
