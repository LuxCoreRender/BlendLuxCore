import bpy
from bpy.types import Panel
from os.path import basename, dirname

def draw_panel_categories(self, context):
    scene = context.scene
    ui_props = scene.luxcore_assets.ui

    name = basename(dirname(dirname(__file__)))
    user_preferences = bpy.context.preferences.addons[name].preferences

    layout = self.layout
    layout.separator()
    layout.label(text='Categories')

    col = layout.column(align=True)

def draw_panel_model_search(self, context):
    scene = context.scene
    model_props = scene.luxcore_assets.model
    layout = self.layout
    col = layout.column(align=True)
    col.prop(model_props, "free_only")

    draw_panel_categories(self, context)

    layout.separator()
    layout.label(text='Import method:')
    col = layout.column()
    col.prop(model_props, 'append_method', expand=True, icon_only=False)

class VIEW3D_PT_LUXCORE_ASSET_LIBRARY(Panel):
    bl_label = "LuxCore Asset Library"
    bl_category = "LuxCoreAssets"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_idname = "VIEW3D_PT_LUXCORE_ASSET_LIBRARY"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        scene = context.scene
        ui_props = scene.luxcore_assets.ui

        layout = self.layout
        name = basename(dirname(dirname(__file__)))
        user_preferences = bpy.context.preferences.addons[name].preferences

        #layout.use_property_split = True
        #layout.use_property_decorate = False

        row = layout.row()
        row.scale_x = 1.6
        row.scale_y = 1.6
        row.prop(ui_props, 'asset_type', expand=True, icon_only=True)

        if bpy.data.filepath == '':
            col = layout.column(align=True)
            col.label(text="It's better to save the file first.")

        if ui_props.asset_type == 'MODEL':
            # noinspection PyCallByClass
            draw_panel_model_search(self, context)
        #elif ui_props.asset_type == 'SCENE':
            # noinspection PyCallByClass
            #draw_panel_scene_search(self, context)
        #elif ui_props.asset_type == 'MATERIAL':
            #draw_panel_material_search(self, context)
        #elif ui_props.asset_type == 'BRUSH':
            #if context.sculpt_object or context.image_paint_object:
                # noinspection PyCallByClass
                #draw_panel_brush_search(self, context)
            #else:
                #label_multiline(layout, text='switch to paint or sculpt mode.', width=context.region.width)


class VIEW3D_PT_LUXCORE_ASSET_LIBRARY_DOWNLOADS(Panel):
    bl_category = "LuxCoreAssets"
    bl_idname = "VIEW3D_PT_LUXCORE_ASSET_LIBRARY_DOWNLOADS"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Downloads"

    @classmethod
    def poll(cls, context):
        #eturn len(download.download_threads) > 0
        return True

    def draw(self, context):
        layout = self.layout
        #TODO
        #for threaddata in download.download_threads:
        #    tcom = threaddata[2]
        #    asset_data = threaddata[1]
        #    row = layout.row()
        #    row.label(text=asset_data['name'])
        #    row.label(text=str(int(tcom.progress)) + ' %')
        #    row.operator('scene.blenderkit_download_kill', text='', icon='CANCEL')
        #    if tcom.passargs.get('retry_counter', 0) > 0:
        #        row = layout.row()
        #        row.label(text='failed. retrying ... ', icon='ERROR')
        #        row.label(text=str(tcom.passargs["retry_counter"]))
        #
        #        layout.separator()
