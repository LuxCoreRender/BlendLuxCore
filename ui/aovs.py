from bl_ui.properties_render_layer import RenderLayerButtonsPanel
from bpy.types import Panel


class LUXCORE_RENDERLAYER_PT_aovs(RenderLayerButtonsPanel, Panel):
    bl_label = "LuxCore Arbitrary Output Variables (AOVs)"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        active_layer = context.scene.render.layers.active
        aovs = active_layer.luxcore.aovs

        layout.label("Basic Information")
        layout.prop(aovs, "rgb")
        layout.prop(aovs, "rgba")
        layout.prop(aovs, "alpha")
        layout.prop(aovs, "depth")

        layout.label("Material/Object Information")
        layout.prop(aovs, "material_id")
        layout.prop(aovs, "object_id")
        layout.prop(aovs, "emission")

        layout.label("Direct Light Information")
        layout.prop(aovs, "direct_diffuse")
        layout.prop(aovs, "direct_glossy")

        layout.label("Indirect Light Information")
        layout.prop(aovs, "indirect_diffuse")
        layout.prop(aovs, "indirect_glossy")
        layout.prop(aovs, "indirect_specular")

        layout.label("Geometry Information")
        layout.prop(aovs, "position")
        layout.prop(aovs, "shading_normal")
        layout.prop(aovs, "geometry_normal")
        layout.prop(aovs, "uv")

        layout.label("Shadow Information")
        layout.prop(aovs, "direct_shadow_mask")
        layout.prop(aovs, "indirect_shadow_mask")

        layout.label("Render Information")
        layout.prop(aovs, "raycount")
        layout.prop(aovs, "samplecount")
        layout.prop(aovs, "convergence")
        layout.prop(aovs, "irradiance")
