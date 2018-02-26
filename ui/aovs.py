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

        split = layout.split()
        col = split.column(align=True)

        col.label("Basic Information")
        col.prop(aovs, "rgb")
        col.prop(aovs, "rgba")
        col.prop(aovs, "alpha")
        col.prop(aovs, "depth")

        col.label("Material/Object Information")
        col.prop(aovs, "material_id")
        col.prop(aovs, "object_id")
        col.prop(aovs, "emission")

        col.label("Direct Light Information")
        col.prop(aovs, "direct_diffuse")
        col.prop(aovs, "direct_glossy")

        col.label("Indirect Light Information")
        col.prop(aovs, "indirect_diffuse")
        col.prop(aovs, "indirect_glossy")
        col.prop(aovs, "indirect_specular")

        col = split.column(align=True)

        col.label("Geometry Information")
        col.prop(aovs, "position")
        col.prop(aovs, "shading_normal")
        col.prop(aovs, "geometry_normal")
        col.prop(aovs, "uv")

        col.label("Shadow Information")
        col.prop(aovs, "direct_shadow_mask")
        col.prop(aovs, "indirect_shadow_mask")

        col.label("Render Information")
        col.prop(aovs, "raycount")
        col.prop(aovs, "samplecount")
        col.prop(aovs, "convergence")
        col.prop(aovs, "irradiance")
