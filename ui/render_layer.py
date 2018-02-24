from bl_ui.properties_render_layer import RenderLayerButtonsPanel
from bpy.types import Panel


class LUXCORE_PT_layer_options(RenderLayerButtonsPanel, Panel):
    bl_label = "Layer"
    COMPAT_ENGINES = {"LUXCORE"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rl = scene.render.layers.active

        split = layout.split()

        col = split.column()
        col.prop(scene, "layers", text="Scene")
        col.prop(rl, "layers_exclude", text="Exclude")

        col = split.column()
        col.prop(rl, "layers", text="Layer")
        #col.prop(rl, "layers_zmask", text="Mask Layer")

        split = layout.split()

        col = split.column()
        col.label(text="Override Material:")
        col.prop(rl, "material_override", text="")

        # TODO: we can add more useful checkboxes here, e.g. hair on/off
