from bl_ui.properties_view_layer import ViewLayerButtonsPanel
from bpy.types import Panel
from .. import utils
from . import icons

class LUXCORE_VIEWLAYER_PT_layer(ViewLayerButtonsPanel, Panel):
    bl_label = "View Layer"
    bl_order = 1
    COMPAT_ENGINES = {"LUXCORE"}

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        layout.use_property_split = True

        scene = context.scene
        rd = scene.render
        layer = context.view_layer

        col = flow.column()
        col.prop(layer, "use", text="Use for Rendering")
        col = flow.column()
        col.prop(rd, "use_single_layer", text="Render Single Layer")


class LUXCORE_VIEWLAYER_PT_override(ViewLayerButtonsPanel, Panel):
    bl_label = "Override"
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = "view_layer"
    bl_order = 3
    COMPAT_ENGINES = {"LUXCORE"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        view_layer = context.view_layer

        layout.prop(view_layer, "material_override")
#         layout.prop(view_layer, "samples")
#         # TODO: we can add more useful checkboxes here, e.g. hair on/off
