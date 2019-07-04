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


##class LUXCORE_VIEWLAYER_PT_layers(ViewLayerButtonsPanel, Panel):
##    bl_label = "Layer List"
##    bl_options = {'HIDE_HEADER'}
##    COMPAT_ENGINES = {"LUXCORE"}
##
##    def draw(self, context):
##        layout = self.layout
##
##        scene = context.scene
###         rd = scene.render
##        window = context.window
##        vl = window.view_layer
##
###        row = layout.row()
###        col = row.column()
###        col.template_list("VIEWLAYER_UL_viewlayers", "", rd, "layers", rd.layers, "active_index", rows=2)
###
###        col = row.column()
###        sub = col.column(align=True)
###        sub.operator("scene.render_layer_add", icon='ZOOMIN', text="")
###        sub.operator("scene.render_layer_remove", icon='ZOOMOUT', text="")
###        col.prop(rd, "use_single_layer", icon_only=True)
##
##        if utils.is_valid_camera(scene.camera):
##            tonemapper = scene.camera.data.luxcore.imagepipeline.tonemapper
##            if len(context.scne.view_layers) > 1 and tonemapper.is_automatic():
##                msg = "Auto tonemapper will cause brightness difference!"
##                layout.label(text=msg, icon=icons.WARNING)
##                layout.operator("luxcore.switch_to_camera_settings", icon=icons.CAMERA)


class LUXCORE_RENDER_PT_override(ViewLayerButtonsPanel, Panel):
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


# class LUXCORE_RENDERLAYER_PT_layer_options(ViewLayerButtonsPanel, Panel):
#     bl_label = "Layer"
#     COMPAT_ENGINES = {"LUXCORE"}
# 
#     def draw(self, context):
#         layout = self.layout
# 
#         window = context.window
#         vl = window.view_layer
#        scene = context.scene
#        rl = scene.render.layers.active
#
#         split = layout.split()
#
#         col = split.column()
#         col.prop(scene, "layers", text="Scene")
#         col.prop(rl, "layers_exclude", text="Exclude")
#
#         col = split.column()
#         col.prop(rl, "layers", text="Layer")
#         #col.prop(rl, "layers_zmask", text="Mask Layer")
#
#         col.label(text="Override Material:")
#         col.prop(rl, "material_override", text="")
#
