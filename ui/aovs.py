from bl_ui.properties_render_layer import RenderLayerButtonsPanel
from bpy.types import Panel


class LUXCORE_RENDERLAYER_PT_aovs(RenderLayerButtonsPanel, Panel):
    bl_label = "LuxCore Arbitrary Output Variables (AOVs)"
    COMPAT_ENGINES = {"LUXCORE"}

    def draw(self, context):
        layout = self.layout
        aovs = context.scene.luxcore.aovs

        layout.prop(aovs, "depth")
        layout.prop(aovs, "samplecount")
