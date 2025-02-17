# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
#
#  This code is based on the Blenderkit Addon
#  Homepage: https://www.blenderkit.com/
#  Sourcecode: https://github.com/blender/blender-addons/tree/master/blenderkit
#
# #####

import bpy
from bpy.types import Panel
from ...utils import get_addon_preferences
from ...utils.lol import utils as utils
from .. import icons


def draw_panel_categories(self, context):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui

    if ui_props.asset_type == 'MODEL':
        asset_props = scene.luxcoreOL.model
    if ui_props.asset_type == 'SCENE':
        asset_props = scene.luxcoreOL.scene
    if ui_props.asset_type == 'MATERIAL':
        asset_props = scene.luxcoreOL.material

    if not 'categories' in asset_props.keys():
        return

    categories = asset_props['categories']

    layout = self.layout
    layout.separator()
    layout.label(text='Categories')

    col = layout.column(align=True)
    op = col.operator('view3d.luxcore_ol_asset_bar', text="All")
    op.do_search = False
    op.keep_running = True

    for cat in categories.keys():
        col = layout.column(align=True)
        ctext = '%s (%i)' % (cat, categories[cat])
        op = col.operator('view3d.luxcore_ol_asset_bar', text=ctext)
        op.do_search = True
        op.keep_running = True
        op.category = cat


def draw_panel_model_search(self, context):
    scene = context.scene
    model_props = scene.luxcoreOL.model
    layout = self.layout

    ui_props = scene.luxcoreOL.ui

    if ui_props.assetbar_on:
        icon = 'HIDE_OFF'
        tooltip = 'Click to Hide Asset Bar'
    else:
        icon = 'HIDE_ON'
        tooltip = 'Click to Show Asset Bar'

    assetbar_operator = layout.operator('view3d.luxcore_ol_asset_bar', text='Asset Bar', icon=icon)

    assetbar_operator.keep_running = False
    assetbar_operator.do_search = False
    assetbar_operator.tooltip = tooltip

    col = layout.column(align=True)
    col.prop(ui_props, 'local', expand=True, icon_only=False)
    col.prop(ui_props, 'free_only', expand=True, icon_only=False)

    draw_panel_categories(self, context)

    layout.separator()
    layout.label(text='Import method:')
    if model_props.switched_append_method:
        col = layout.column()
        col.text()
    col = layout.column()
    col.prop(model_props, 'append_method', expand=True, icon_only=False)


def draw_panel_scene_search(self, context):
    scene = context.scene
    layout = self.layout
    ui_props = scene.luxcoreOL.ui

    if ui_props.assetbar_on:
        icon = 'HIDE_OFF'
        tooltip = 'Click to Hide Asset Bar'
    else:
        icon = 'HIDE_ON'
        tooltip = 'Click to Show Asset Bar'

    assetbar_operator = layout.operator('view3d.luxcore_ol_asset_bar', text='Asset Bar', icon=icon)
    assetbar_operator.keep_running = False
    assetbar_operator.do_search = False
    assetbar_operator.tooltip = tooltip

    col = layout.column(align=True)
    col.prop(ui_props, 'local', expand=True, icon_only=False)
    col.prop(ui_props, 'free_only', expand=True, icon_only=False)


def draw_panel_material_search(self, context):
    scene = context.scene
    layout = self.layout

    ui_props = scene.luxcoreOL.ui

    if ui_props.assetbar_on:
        icon = 'HIDE_OFF'
        tooltip = 'Click to Hide Asset Bar'
    else:
        icon = 'HIDE_ON'
        tooltip = 'Click to Show Asset Bar'

    assetbar_operator = layout.operator('view3d.luxcore_ol_asset_bar', text='Asset Bar', icon=icon)
    assetbar_operator.keep_running = False
    assetbar_operator.do_search = False
    assetbar_operator.tooltip = tooltip

    col = layout.column(align=True)
    col.prop(ui_props, 'local', expand=True, icon_only=False)
    col.prop(ui_props, 'free_only', expand=True, icon_only=False)

    draw_panel_categories(self, context)


class VIEW3D_PT_LUXCORE_ONLINE_LIBRARY(Panel):
    bl_label = "LuxCore Online Library"
    bl_category = "LuxCoreOnlineLibrary"
    #bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_idname = "VIEW3D_PT_LUXCORE_ONLINE_LIBRARY"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        user_preferences = get_addon_preferences(context)

        return user_preferences.use_library

    def draw(self, context):
        scene = context.scene
        ui_props = scene.luxcoreOL.ui

        layout = self.layout

        col = layout.column(align=True)
        col.scale_x = 1.4
        col.scale_y = 1.4
        op = col.operator("luxcore.open_website", icon=icons.URL, text="Donation (Blendermarket)")
        op.url = "https://blendermarket.com/creators/draviastudio"
        op = col.operator("luxcore.open_website", icon=icons.URL, text="Donation (CG Trader)")
        op.url = "https://www.cgtrader.com/draviastudio"

        col = layout.column(align=True)
        col.scale_x = 1.4
        col.scale_y = 1.4
        op = col.operator("luxcore.open_website", icon=icons.URL, text="License: CC-BY-SA")
        op.url = "https://github.com/LuxCoreRender/LoL/blob/master/COPYING.txt"

        layout.separator()

        #TODO: implement additional modes, i.e. material, textures, brushes if needed
        row = layout.row()
        row.scale_x = 1.6
        row.scale_y = 1.6
        row.prop(ui_props, 'asset_type', expand=True, icon_only=True)

        if bpy.data.filepath == '':
            col = layout.column(align=True)
            col.label(text="It's better to save the file first.")

        layout.operator('scene.luxcore_ol_update_toc', text='Update ToC from server')
        if ui_props.asset_type == 'MODEL':
            draw_panel_model_search(self, context)
        elif ui_props.asset_type == 'SCENE':
            draw_panel_scene_search(self, context)
        elif ui_props.asset_type == 'MATERIAL':
            draw_panel_material_search(self, context)
        #elif ui_props.asset_type == 'BRUSH':
            #if context.sculpt_object or context.image_paint_object:
                #draw_panel_brush_search(self, context)
            #else:
                #label_multiline(layout, text='switch to paint or sculpt mode.', width=context.region.width)


class VIEW3D_PT_LUXCORE_ONLINE_LIBRARY_DOWNLOADS(Panel):
    bl_category = "LuxCoreOnlineLibrary"
    bl_idname = "VIEW3D_PT_LUXCORE_ONLINE_LIBRARY_DOWNLOADS"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Downloads"
    bl_order = 3

    @classmethod
    def poll(cls, context):
        user_preferences = get_addon_preferences(context)

        return len(utils.download_threads) > 0 and user_preferences.use_library

    def draw(self, context):
        layout = self.layout

        for idx, threaddata in enumerate(utils.download_threads):
           tcom = threaddata[2]
           asset_data = threaddata[1]

           row = layout.row()
           row.label(text=asset_data['name'])
           row.label(text=str(int(tcom.progress)) + ' %')
           row.operator('scene.luxcore_ol_download_kill', text='', icon='CANCEL').thread_index = idx

           # TODO: Implement retry download
           # if tcom.passargs.get('retry_counter', 0) > 0:
           #     row = layout.row()
           #     row.label(text='failed. retrying ... ', icon='ERROR')
           #     row.label(text=str(tcom.passargs["retry_counter"]))
           #
           #     layout.separator()


class VIEW3D_PT_LUXCORE_ONLINE_LIBRARY_LOCAL(Panel):
    bl_category = "LuxCoreOnlineLibrary"
    bl_idname = "VIEW3D_PT_LUXCORE_ONLINE_LIBRARY_LOCAL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Local"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        user_preferences = get_addon_preferences(context)

        return user_preferences.use_library

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        upload_props = context.scene.luxcoreOL.upload
        ui_props = context.scene.luxcoreOL.ui

        if ui_props.asset_type == "MATERIAL":
            obj = context.active_object
            if obj:
                is_sortable = len(obj.material_slots) > 1
                rows = 1
                if (is_sortable):
                    rows = 4

                col = layout.column(align=True)
                col.label(text="Material:")
                col = layout.column(align=True)
                col.template_list("MATERIAL_UL_matslots", "", obj, "material_slots", obj, "active_material_index",
                                  rows=rows)
        else:
            col = layout.column(align=True)
            col.prop(upload_props, 'name')

        col = layout.column(align=True)
        col.prop(upload_props, 'category')

        col = layout.column(align=True)
        col.prop(upload_props, 'autorender')
        if upload_props.autorender:
            col = layout.column(align=True)
            col.prop(upload_props, "samples")

        col = layout.column(align=True)
        col.label(text="Thumbnail:")

        if not upload_props.autorender:
            col = layout.column(align=True)
            col.prop(upload_props, "show_thumbnail", icon=icons.IMAGE)

            if upload_props.show_thumbnail:
                layout.template_ID_preview(upload_props, "thumbnail", open="image.open")
            else:
                layout.template_ID(upload_props, "thumbnail", open="image.open")

        if (upload_props.thumbnail is None and not upload_props.autorender):
            col2 = layout.column(align=True)
            col2.label(text="No thumbnail available", icon=icons.WARNING)

        col = layout.column(align=True)
        col.enabled = (upload_props.thumbnail is not None or upload_props.autorender)
        col.operator("scene.luxcore_ol_add_local", text="Add asset...")
        col = layout.column(align=True)
        col.operator("scene.luxcore_ol_scan_local", text="Search new local assets")


def settings_toggle_icon(enabled):
    return icons.EXPANDABLE_OPENED if enabled else icons.EXPANDABLE_CLOSED


class VIEW3D_PT_LUXCORE_ONLINE_LIBRARY_SCAN_RESULT(Panel):
    bl_category = "LuxCoreOnlineLibrary"
    bl_idname = "VIEW3D_PT_LUXCORE_ONLINE_LIBRARY_SCAN_RESULT"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Scan Result"
    bl_order = 3

    @classmethod
    def poll(self, context):
        user_preferences = get_addon_preferences(context)

        return len(context.scene.luxcoreOL.upload.add_list) > 0 and user_preferences.use_library

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        upload_props = context.scene.luxcoreOL.upload
        ui_props = context.scene.luxcoreOL.ui

        # if ui_props.asset_type == "MATERIAL":
        #
        # else:
        #

        for idx, asset in enumerate(upload_props.add_list):
            self.draw_addlist(layout, asset, idx)

    def draw_addlist(self, layout, asset, idx):
        col = layout.column(align=True)
        # Upper row (enable/disable, name, remove)
        box = col.box()
        row = box.row()
        col = row.column()

        col.prop(asset, "show_settings",
                 icon=settings_toggle_icon(asset.show_settings),
                 icon_only=True, emboss=False)
        col = row.column()
        col.prop(asset, "name", text="")
        # op = row.operator("scene.luxcore_ol_remove_asset",
        #                   text="", icon=icons.CLEAR, emboss=False)
        # op.index = idx

        if asset.show_settings:
            col = box.column(align=True)
            col.prop(asset, "category")

            col = box.column(align=True)
            col.label(text="Thumbnail:")
            col.prop(asset, "show_thumbnail", icon=icons.IMAGE)

            if asset.show_thumbnail:
                col.template_ID_preview(asset, "thumbnail", open="image.open")
            else:
                col.template_ID(asset, "thumbnail", open="image.open")

            col = box.column(align=True)
            col.enabled = (asset.thumbnail is not None)
            op = col.operator("scene.luxcore_ol_add_local", text="Add asset...")
            op.asset_index = idx