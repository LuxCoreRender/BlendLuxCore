from bl_ui.properties_render_layer import RenderLayerButtonsPanel
from bpy.types import Panel
from ..ui import icons


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

        # Supported by BIDIR
        col.label("Basic Information")
        col.prop(aovs, "rgb")
        col.prop(aovs, "rgba")
        col.prop(aovs, "alpha")
        col.prop(aovs, "depth")
        col.prop(aovs, "albedo")

        # Supported by BIDIR
        col.label("Material/Object Information")
        col.prop(aovs, "material_id")
        col.prop(aovs, "material_id_color")
        col.prop(aovs, "object_id")
        # Not supported by BIDIR
        sub = col.column(align=True)
        sub.active = engine_is_path
        sub.prop(aovs, "emission")

        # Not supported by BIDIR
        sub.label("Direct Light Information")
        sub.prop(aovs, "direct_diffuse")
        sub.prop(aovs, "direct_glossy")

        # Not supported by BIDIR
        sub.label("Indirect Light Information")
        sub.prop(aovs, "indirect_diffuse")
        sub.prop(aovs, "indirect_glossy")
        sub.prop(aovs, "indirect_specular")

        col = split.column(align=True)

        # Supported by BIDIR
        col.label("Geometry Information")
        col.prop(aovs, "position")
        col.prop(aovs, "shading_normal")
        col.prop(aovs, "avg_shading_normal")
        col.prop(aovs, "geometry_normal")
        col.prop(aovs, "uv")

        # Not supported by BIDIR
        sub = col.column(align=True)
        sub.active = engine_is_path
        sub.label("Shadow Information")
        sub.prop(aovs, "direct_shadow_mask")
        sub.prop(aovs, "indirect_shadow_mask")

        # Not supported by BIDIR
        sub.label("Render Information")
        sub.prop(aovs, "irradiance")
        sub.prop(aovs, "raycount")

        # Supported by BIDIR
        col.prop(aovs, "convergence")
        col.prop(aovs, "noise")
        col.prop(aovs, "samplecount")
