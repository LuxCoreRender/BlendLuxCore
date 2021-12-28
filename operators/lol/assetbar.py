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
from bpy.types import Operator
from bpy.props import BoolProperty, IntProperty, StringProperty
import math
from mathutils import Vector

from ...utils import get_addon_preferences
from ...utils.lol import utils as utils
from ...draw.lol import viewport as ui_bgl
from bpy_extras import view3d_utils


handler_2d = None
handler_3d = None
active_area = None
active_window = None
active_region = None

def draw_callback_2d(self, context):
    area = context.area
    window = context.window
    try:
        # self.area might throw error just by itself.
        area1 = self.area
        window1 = self.window
        go = True
        if len(area.spaces[0].region_quadviews) > 0:
            if area.spaces[0].region_3d != context.region_data:
                go = False

    except:
        go = False

    if go and area == area1 and window == window1:
        draw_callback_2d_search(self, context)


def draw_callback_2d_progress(self, context):
    index = 0
    for threaddata in utils.download_threads:
        tcom = threaddata[2]

        asset_data = threaddata[1]

        img = utils.get_thumbnail('thumbnail_notready.jpg')
        if 'thumbnail' in asset_data.keys() and asset_data['thumbnail'] != None and asset_data['thumbnail'].size[0] != 0:
            img = asset_data['thumbnail']

        if tcom.passargs.get('downloaders'):
            for d in tcom.passargs['downloaders']:

                loc = view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d,
                                                            d['location'])
                if loc is not None:
                    ui_bgl.draw_downloader(loc[0], loc[1], tcom.progress, img)


def draw_callback_3d_progress(self, context):
    for threaddata in utils.download_threads:
        tcom = threaddata[2]

        asset_data = threaddata[1]
        if tcom.passargs['asset type'] == 'MODEL':
            bbox_min = Vector(asset_data["bbox_min"])
            bbox_max = Vector(asset_data["bbox_max"])
            bbox_center = 0.5 * Vector((bbox_max[0] + bbox_min[0], bbox_max[1] + bbox_min[1], 0.0))

            if tcom.passargs.get('downloaders'):
                for d in tcom.passargs['downloaders']:
                    ui_bgl.draw_bbox(d['location'], d['rotation'], bbox_min-bbox_center, bbox_max-bbox_center,
                                   progress=tcom.progress)


def draw_callback_3d(self, context):
    ''' Draw snapped bbox while dragging'''

    ui_props = context.scene.luxcoreOL.ui

    if ui_props.dragging and ui_props.asset_type == 'MODEL':
        if ui_props.draw_snapped_bounds:
            bbox_min = Vector(ui_props.snapped_bbox_min)
            bbox_max = Vector(ui_props.snapped_bbox_max)
            bbox_center = 0.5 * Vector((bbox_max[0] + bbox_min[0], bbox_max[1] + bbox_min[1], 0.0))

            ui_bgl.draw_bbox(ui_props.snapped_location, ui_props.snapped_rotation, bbox_min-bbox_center, bbox_max-bbox_center)


def draw_callback_2d_search(self, context):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui
    assetbar_props = scene.luxcoreOL.ui.assetbar
    assets = utils.get_search_props(context)

    if ui_props.local:
        assets = [asset for asset in assets if asset['local']]

    if ui_props.free_only:
        assets = [asset for asset in assets if not asset['locked']]

    if scene.luxcoreOL.on_search:
        assets = [asset for asset in assets if asset['category'] == scene.luxcoreOL.search_category]

    region = self.region
    hcolor = (1, 1, 1, .07)
    grey = (hcolor[0] * .8, hcolor[1] * .8, hcolor[2] * .8, .5)
    white = (1, 1, 1, 0.2)
    green = (.2, 1, .2, .7)
    highlight = (1, 1, 1, .3)

    # background of asset bar

    if not ui_props.dragging:
        if len(assets) == 0 or assetbar_props.wcount == 0:
            return

        h_draw = min(assetbar_props.hcount, math.ceil(len(assets) / assetbar_props.wcount))

        row_height = ui_props.thumb_size + assetbar_props.margin
        ui_bgl.draw_rect(assetbar_props.x, assetbar_props.y - assetbar_props.height, assetbar_props.width,
                         assetbar_props.height, hcolor)

        if len(assets) != 0:
            if ui_props.scrolloffset > 0 or assetbar_props.wcount * assetbar_props.hcount < len(assets):
                assetbar_props.drawoffset = 25
            else:
                assetbar_props.drawoffset = 0

            # Draw scroll arrows
            if assetbar_props.wcount * assetbar_props.hcount < len(assets):
                arrow_y = assetbar_props.y - int((assetbar_props.height + ui_props.thumb_size) / 2) + assetbar_props.margin
                if ui_props.scrolloffset > 0:

                    if ui_props.active_index == -2:
                        ui_bgl.draw_rect(assetbar_props.x, assetbar_props.y - assetbar_props.height, 25,
                                         assetbar_props.height, highlight)

                    ui_bgl.draw_image(assetbar_props.x, arrow_y, 25,
                                      ui_props.thumb_size, utils.get_thumbnail('arrow_left.png'), 1)

                if len(assets) - ui_props.scrolloffset > (assetbar_props.wcount * assetbar_props.hcount):
                    if ui_props.active_index == -1:
                        ui_bgl.draw_rect(assetbar_props.x + assetbar_props.width - 25,
                                         assetbar_props.y - assetbar_props.height, 25,
                                         assetbar_props.height, highlight)

                    ui_bgl.draw_image(assetbar_props.x + assetbar_props.width - 25, arrow_y, 25,
                                      ui_props.thumb_size, utils.get_thumbnail('arrow_right.png'), 1)


            # Draw asset thumbnails
            for b in range(0, h_draw):
                w_draw = min(assetbar_props.wcount, len(assets) - b * assetbar_props.wcount - ui_props.scrolloffset)

                y = assetbar_props.y - (b + 1) * (row_height)
                for a in range(0, w_draw):
                    x = assetbar_props.x + a * (
                            assetbar_props.margin + ui_props.thumb_size) + assetbar_props.margin + assetbar_props.drawoffset

                    index = a + ui_props.scrolloffset + b * assetbar_props.wcount

                    img = utils.get_thumbnail('thumbnail_notready.jpg')
                    asset = assets[index]
                    if 'thumbnail' in asset.keys() and asset['thumbnail'] != None and asset['thumbnail'].size[0] != 0:
                        img = asset['thumbnail']

                    w = int(ui_props.thumb_size * img.size[0] / max(img.size[0], img.size[1]))
                    h = int(ui_props.thumb_size * img.size[1] / max(img.size[0], img.size[1]))
                    crop = (0, 0, 1, 1)

                    if img.size[0] > img.size[1]:
                        offset = (1 - img.size[1] / img.size[0]) / 2
                        crop = (offset, 0, 1 - offset, 1)

                    if img is not None:
                        ui_bgl.draw_image(x, y, w, w, img, 1, crop=crop)
                        if index == ui_props.active_index:
                            ui_bgl.draw_rect(x - assetbar_props.highlight_margin, y - assetbar_props.highlight_margin,
                                             w + 2 * assetbar_props.highlight_margin, w + 2 * assetbar_props.highlight_margin,
                                             highlight)
                    else:
                        ui_bgl.draw_rect(x, y, w, h, white)

                    if assets[index]['downloaded'] > 0:
                        ui_bgl.draw_rect(x - assetbar_props.highlight_margin, y - assetbar_props.highlight_margin, int(w * assets[index]['downloaded'] / 100.0), 2, green)

                    if assets[index]['patreon']:
                        #img = utils.get_thumbnail('blender_market.png')
                        img = utils.get_thumbnail('cgtrader.png')

                        ui_bgl.draw_image(x + w - 24 - 2, y + w - 24 - 2, 24, 24, img, 1)
                        if assets[index]['locked']:
                            img = utils.get_thumbnail('locked.png')
                            ui_bgl.draw_image(x + 2, y + 2, 24, 24, img, 1)

            # Show tooltip box with additional asset information
            if -1 < ui_props.active_index < len(assets):
                asset = assets[ui_props.active_index]
                licence = '\n\nLicence: royality free' if asset['patreon'] else '\n\nLicence: CC-BY-SA'
                tooltip = asset['name'] + '\n\nCategory: ' + asset['category'] + licence
                atip = '\n\nhttps://blendermarket.com/creators/draviastudio\nhttps://www.cgtrader.com/draviastudio\n'


                if asset['local']:
                    tooltip = asset['name'] + '\n\nCategory: ' + asset['category']
                    atip = ''

                gimg = None

                draw_tooltip(context, ui_props.mouse_x, ui_props.mouse_y, text=tooltip, author=atip,
                             asset=asset, gravatar=gimg)

    # Scroll assets with mouse wheel
    if ui_props.dragging and (
            ui_props.draw_drag_image or ui_props.draw_snapped_bounds) and ui_props.active_index > -1:

        if assets[ui_props.active_index]['patreon'] and assets[ui_props.active_index]['locked']:
            img = utils.get_thumbnail('delete.png')
        else:
            img = assets[ui_props.active_index]['thumbnail']

        if img is None:
            img = utils.get_thumbnail('thumbnail_notready.jpg')

        linelength = 35

        ui_bgl.draw_image(ui_props.mouse_x + linelength, ui_props.mouse_y - linelength - 50,
                          50, 50, img, 1)
        ui_bgl.draw_line2d(ui_props.mouse_x, ui_props.mouse_y, ui_props.mouse_x + linelength,
                           ui_props.mouse_y - linelength, 2, white)


def draw_tooltip(context, x, y, text='', author='', asset=None, gravatar=None):
    region = context.region
    scale = context.preferences.view.ui_scale
    ui_props = context.scene.luxcoreOL.ui
    user_preferences = get_addon_preferences(context)

    ttipmargin = 2
    textmargin = 10

    font_height = int(12 * scale)
    line_height = int(15 * scale)
    nameline_height = int(23 * scale)

    lines = text.split('\n')
    alines = author.split('\n')
    ncolumns = 2

    nlines = max(len(lines) - 1, len(alines))

    texth = line_height * nlines + nameline_height

    from os.path import join, splitext
    import os

    if ui_props.asset_type == 'MATERIAL':
        imagename = asset['name'].replace(" ", "_") + '.jpg'
    else:
        imagename = splitext(asset['url'])[0] + '.jpg'

    tpath = join(user_preferences.global_dir, ui_props.asset_type.lower(), 'preview', 'full',
                 imagename)
    img = utils.get_thumbnail('thumbnail_notready.jpg')

    if os.path.exists(tpath) and os.path.getsize(tpath) > 0:
        img = bpy.data.images.get('.LOL_preview_full')
        if img is not None:
            bpy.data.images.remove(img)
        img = bpy.data.images.load(tpath)
        img.name = '.LOL_preview_full'

    #TODO: Load full preview image if it is not available locally

    if max(img.size[0], img.size[1]) == 0:
        return
    isizex = int(512 * scale * img.size[0] / max(img.size[0], img.size[1]))
    isizey = int(512 * scale * img.size[1] / max(img.size[0], img.size[1]))

    estimated_height = 2 * ttipmargin + textmargin + isizey

    if estimated_height > y:
        scaledown = y / (estimated_height)
        scale *= scaledown
        # we need to scale these down to have correct size if the tooltip wouldn't fit.
        font_height = int(12 * scale)
        line_height = int(15 * scale)
        nameline_height = int(23 * scale)

        lines = text.split('\n')

        texth = line_height * nlines + nameline_height
        isizex = int(512 * scale * img.size[0] / max(img.size[0], img.size[1]))
        isizey = int(512 * scale * img.size[1] / max(img.size[0], img.size[1]))

    name_height = int(18 * scale)

    x += 2 * ttipmargin
    y -= 2 * ttipmargin

    width = isizex + 2 * ttipmargin

    properties_width = 0
    for r in bpy.context.area.regions:
        if r.type == 'UI':
            properties_width = r.width

    x = min(x + width, region.width - properties_width) - width

    bgcol = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.inner
    bgcol1 = (bgcol[0], bgcol[1], bgcol[2], .6)
    textcol = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.text
    textcol = (textcol[0], textcol[1], textcol[2], 1)
    textcol_mild = (textcol[0] * .8, textcol[1] * .8, textcol[2] * .8, 1)
    textcol_strong = (textcol[0] * 1.3, textcol[1] * 1.3, textcol[2] * 1.3, 1)
    white = (1, 1, 1, .1)

    # background
    ui_bgl.draw_rect(x - ttipmargin, y - 2 * ttipmargin - isizey,
                     isizex + ttipmargin * 2, 2 * ttipmargin + isizey, bgcol)
    # main preview image
    ui_bgl.draw_image(x, y - isizey - ttipmargin, isizex, isizey, img, 1)


    # draw blendermarket logo for purchased assets and locked symbol for not purchased assets
    if asset['patreon']:
        #img = utils.get_thumbnail('blender_market.png')
        img = utils.get_thumbnail('cgtrader.png')
        ui_bgl.draw_image(x + isizex - 52*scale - 2, y - 52*scale - ttipmargin - 2, 52*scale, 52*scale, img, 1)
        if asset['locked']:
            img = utils.get_thumbnail('locked.png')
            ui_bgl.draw_image(x + 2, y - 52*scale - ttipmargin - 2, 52*scale, 52*scale, img, 1)

    # text overlay background
    ui_bgl.draw_rect(x - ttipmargin,
                     y - 2 * ttipmargin - isizey,
                     isizex + ttipmargin * 2,
                     2 * ttipmargin + texth,
                     bgcol1)
    # draw gravatar
    gsize = 40
    if gravatar is not None:
        ui_bgl.draw_image(x + isizex / 2 + textmargin, y - isizey + texth - gsize - nameline_height - textmargin,
                          gsize, gsize, gravatar, 1)

    i = 0
    column_lines = -1  # start minus one for the name
    xtext = x + textmargin
    fsize = name_height
    tcol = textcol

    for l in lines:
        ytext = y - column_lines * line_height - nameline_height - ttipmargin - textmargin - isizey + texth
        if i == 0:
            ytext = y - name_height + 5 - isizey + texth - textmargin
        elif i == len(lines) - 1:
            ytext = y - (nlines - 1) * line_height - nameline_height - ttipmargin * 2 - isizey + texth
            tcol = textcol
            fsize = font_height
        else:
            if l[:4] == 'Tip:':
                tcol = textcol_strong
            fsize = font_height
        i += 1
        column_lines += 1
        ui_bgl.draw_text(l, xtext, ytext, fsize, tcol)

    xtext += int(isizex / ncolumns) - 30

    column_lines = 1
    for l in alines:
        if gravatar is not None:
            if column_lines == 1:
                xtext += gsize + textmargin
            if column_lines == 4:
                xtext -= gsize + textmargin

        ytext = y - column_lines * line_height - nameline_height - ttipmargin - textmargin - isizey + texth
        if i == 0:
            ytext = y - name_height + 5 - isizey + texth - textmargin
        elif i == len(lines) - 1:
            ytext = y - (nlines - 1) * line_height - nameline_height - ttipmargin * 2 - isizey + texth
            tcol = textcol
            fsize = font_height
        else:
            if l[:4] == 'Tip:':
                tcol = textcol_strong
            fsize = font_height
        i += 1
        column_lines += 1
        ui_bgl.draw_text(l, xtext, ytext, fsize, tcol)


class LOLAssetBarOperator(Operator):
    bl_idname = "view3d.luxcore_ol_asset_bar"
    bl_label = "LuxCore Online Library Asset Bar UI"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    do_search: BoolProperty(name="Run Search", description='', default=True, options={'SKIP_SAVE'})
    keep_running: BoolProperty(name="Keep Running", description='', default=True, options={'SKIP_SAVE'})
    free_only: BoolProperty(name="Free Only", description='', default=False, options={'SKIP_SAVE'})
    tooltip: bpy.props.StringProperty(default='runs search and displays the asset bar at the same time')
    category: StringProperty(name="Category", description="search only subtree of this category",
        default="", options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        scene = context.scene
        ui_props = scene.luxcoreOL.ui
        assetbar_props = ui_props.assetbar

        user_preferences = get_addon_preferences(context)

        if not user_preferences.use_library:
            return {'CANCELLED'}

        ui_props.drag_init = False
        ui_props.dragging = False

        assetbar_props.drag_init = False
        assetbar_props.dragging = False
        assetbar_props.resize_x_left = False
        assetbar_props.resize_x_right = False
        assetbar_props.resize_y_top = False
        assetbar_props.resize_y_down = False

        scene.luxcoreOL.search_category = ""
        scene.luxcoreOL.on_search = self.do_search

        if not ui_props.ToC_loaded:
            if not utils.download_table_of_contents(context):
                return {'CANCELLED'}

        assets = utils.get_search_props(context)

        if ui_props.asset_type == 'MODEL':
            if not scene.luxcoreOL.model.thumbnails_loaded:
                utils.load_previews(context, ui_props.asset_type)
                scene.luxcoreOL.model.thumbnails_loaded = True

        elif ui_props.asset_type == 'MATERIAL':
            if not scene.luxcoreOL.material.thumbnails_loaded:
                utils.load_previews(context, ui_props.asset_type)
                scene.luxcoreOL.material.thumbnails_loaded = True

        ui_props.scrolloffset = 0

        if ui_props.local:
            assets = [asset for asset in assets if asset['local']]

        if ui_props.free_only:
            assets = [asset for asset in assets if not asset['locked']]

        if scene.luxcoreOL.on_search:
            assets = [asset for asset in assets if asset['category'] == scene.luxcoreOL.search_category]
            scene.luxcoreOL.search_category = self.category

        if ui_props.assetbar_on:
            if not self.keep_running:
                ui_props.turn_off = True
                ui_props.assetbar_on = False
            else:
                pass
            return {'FINISHED'}

        ui_props.assetbar_on = True

        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            ui_props.turn_off = True
            ui_props.assetbar_on = False
            return {'CANCELLED'}

        # the arguments we pass the the callback
        args = (self, context)

        self.window = context.window
        self.area = context.area
        self.scene = bpy.context.scene

        self.has_quad_views = len(bpy.context.area.spaces[0].region_quadviews) > 0
        for r in self.area.regions:
            if r.type == 'WINDOW':
                self.region = r
                break

        global active_window, active_area, active_region
        active_window = self.window
        active_area = self.area
        active_region = self.region

        ui_bgl.init_ui_size(context, active_area, active_region)

        self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d, args, 'WINDOW', 'POST_PIXEL')
        self._handle_2d_progress = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d_progress, args, 'WINDOW', 'POST_PIXEL')
        self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d, args, 'WINDOW', 'POST_VIEW')
        self._handle_3d_progress = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d_progress, args, 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def exit_modal(self):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
        except:
            pass

        self.area.tag_redraw()

    def modal(self, context, event):
        scene = context.scene
        ui_props = context.scene.luxcoreOL.ui
        assetbar_props = ui_props.assetbar

        user_preferences = get_addon_preferences(context)
        assets = utils.get_search_props(context)
        context.window.cursor_set("DEFAULT")

        if not user_preferences.use_library:
            return {'CANCELLED'}

        if ui_props.local:
            assets = [asset for asset in assets if asset['local']]

        if ui_props.free_only:
            assets = [asset for asset in assets if not asset['locked']]

        if scene.luxcoreOL.on_search:
            assets = [asset for asset in assets if asset['category'] == scene.luxcoreOL.search_category]

        areas = []

        if bpy.context.scene != self.scene:
            self.exit_modal()
            return {'CANCELLED'}

        for w in context.window_manager.windows:
            areas.extend(w.screen.areas)

        if self.area not in areas or self.area.type != 'VIEW_3D' or self.has_quad_views != (
                len(self.area.spaces[0].region_quadviews) > 0):
            # stopping here model by now - because of:
            #   switching layouts or maximizing area now fails to assign new area throwing the bug
            #   internal error: modal gizmo-map handler has invalid area
            self.exit_modal()
            return {'CANCELLED'}

            newarea = None
            for a in context.window.screen.areas:
                if a.type == 'VIEW_3D':
                    self.area = a
                    for r in a.regions:
                        if r.type == 'WINDOW':
                            self.region = r
                    newarea = a
                    break

            # we check again and quit if things weren't fixed this way.
            if newarea == None:
                self.exit_modal()
                ui_props.assetbar_on = False
                return {'CANCELLED'}

        if not assetbar_props.wcount > 0:
            ui_props.turn_off = True

        if ui_props.turn_off:
            ui_props.assetbar_on = False
            ui_props.turn_off = False
            self.exit_modal()
            ui_props.draw_tooltip = False
            return {'CANCELLED'}

        ui_bgl.update_ui_size(context, active_area, active_region)
        self.area.tag_redraw()

        if event.type == 'WHEELUPMOUSE' or event.type == 'WHEELDOWNMOUSE' or event.type == 'TRACKPADPAN':
            # Scrolling
            mx = event.mouse_region_x
            my = event.mouse_region_y


            if ui_props.dragging and not ui_bgl.mouse_in_asset_bar(context, mx, my):
                # and my < r.height - assetbar_props.height \
                # and mx > 0 and mx < r.width and my > 0:
                context.window.cursor_set("NONE")

                sprops = bpy.context.scene.luxcoreOL.model
                if event.type == 'WHEELUPMOUSE':
                    sprops.offset_rotation_amount += sprops.offset_rotation_step
                elif event.type == 'WHEELDOWNMOUSE':
                    sprops.offset_rotation_amount -= sprops.offset_rotation_step

                #### TODO - this snapping code below is 3x in this file.... refactor it.
                ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = ui_bgl.mouse_raycast(
                    context, mx, my)

                # MODELS can be dragged on scene floor
                if not ui_props.has_hit and ui_props.asset_type == 'MODEL':
                    ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = ui_bgl.floor_raycast(
                        context, mx, my)

                return {'RUNNING_MODAL'}

            if not ui_bgl.mouse_in_asset_bar(context, mx, my):
                return {'PASS_THROUGH'}

            if event.ctrl and ui_bgl.mouse_in_asset_bar(context, mx, my):
                if event.type == 'WHEELDOWNMOUSE':
                    ui_props.thumb_size = min(256, ui_props.thumb_size + 8)

                elif event.type == 'WHEELUPMOUSE':
                    ui_props.thumb_size = max(48, ui_props.thumb_size - 8)
                return {'RUNNING_MODAL'}

            if (event.type == 'WHEELDOWNMOUSE') and len(assets) - ui_props.scrolloffset > (
                    assetbar_props.wcount * assetbar_props.hcount):
                if assetbar_props.hcount > 1:
                    ui_props.scrolloffset += assetbar_props.wcount
                else:
                    ui_props.scrolloffset += 1
                if len(assets) - ui_props.scrolloffset < (assetbar_props.wcount * assetbar_props.hcount):
                    ui_props.scrolloffset = len(assets) - (assetbar_props.wcount * assetbar_props.hcount)

            if event.type == 'WHEELUPMOUSE' and ui_props.scrolloffset > 0:
                if assetbar_props.hcount > 1:
                    ui_props.scrolloffset -= assetbar_props.wcount
                else:
                    ui_props.scrolloffset -= 1
                if ui_props.scrolloffset < 0:
                    ui_props.scrolloffset = 0

            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE':  # Apply
            region = self.region
            mx = event.mouse_region_x
            my = event.mouse_region_y

            ui_props.mouse_x = mx
            ui_props.mouse_y = my

            if assetbar_props.resize_x_right:
                if (assetbar_props.start + assetbar_props.x_offset + assetbar_props.resize_wh + mx) <= region.width - assetbar_props.end:
                    assetbar_props.width = max(assetbar_props.resize_wh + mx, 2*assetbar_props.margin + ui_props.thumb_size + 50)
                context.window.cursor_set("MOVE_X")
                return {'RUNNING_MODAL'}

            elif assetbar_props.resize_x_left:
                if assetbar_props.resize_wh - assetbar_props.resize_xy - mx >= 2 * assetbar_props.margin + ui_props.thumb_size + 50:
                    assetbar_props.x_offset = assetbar_props.resize_xy + mx
                    assetbar_props.width = assetbar_props.resize_wh - assetbar_props.x_offset
                context.window.cursor_set("MOVE_X")
                return {'RUNNING_MODAL'}

            if assetbar_props.resize_y_top:
                if region.height - assetbar_props.resize_xy + my - assetbar_props.resize_wh >= 2*assetbar_props.margin + ui_props.thumb_size:
                    assetbar_props.y_offset = assetbar_props.resize_xy - my
                    assetbar_props.height = region.height - assetbar_props.y_offset - assetbar_props.resize_wh

                context.window.cursor_set("MOVE_Y")
                return {'RUNNING_MODAL'}

            elif assetbar_props.resize_y_down:
                assetbar_props.height = max(assetbar_props.resize_wh - my, 2*assetbar_props.margin + ui_props.thumb_size)
                context.window.cursor_set("MOVE_Y")
                return {'RUNNING_MODAL'}

            if ui_bgl.mouse_in_asset_bar(context, mx, my):
                if (mx - assetbar_props.x_offset - assetbar_props.start - assetbar_props.width + 1 <= 0) and \
                        (mx - assetbar_props.x_offset - assetbar_props.start - assetbar_props.width + 1) >= -2:
                    context.window.cursor_set("MOVE_X")

                if (mx - assetbar_props.x_offset-assetbar_props.start - 1) <= 2 and \
                        (mx - assetbar_props.x_offset-assetbar_props.start - 1) >= 0:
                    context.window.cursor_set("MOVE_X")

                if (region.height - assetbar_props.y_offset - my - 1) >= 0 and \
                        (region.height - assetbar_props.y_offset - my - 1) <= 2:
                    context.window.cursor_set("MOVE_Y")

                if (region.height - assetbar_props.y_offset - my - assetbar_props.height + 1) <= 0 and \
                        (region.height - assetbar_props.y_offset - my - assetbar_props.height + 1) >= -2:
                    context.window.cursor_set("MOVE_Y")

            # Start dragging an asset into the 3D scene
            if ui_props.drag_init:
                ui_props.drag_length += 1
                if ui_props.drag_length > 0:
                    ui_props.dragging = True
                    ui_props.drag_init = False

            # Init dragging the assetbar
            if assetbar_props.drag_init:
                if abs(assetbar_props.drag_x - ui_props.mouse_x) + abs(assetbar_props.drag_y - ui_props.mouse_y) > 0:
                    assetbar_props.dragging = True
                    assetbar_props.drag_init = False

            # Dragging the assetbar
            if assetbar_props.dragging:
                context.window.cursor_set("HAND")
                if (assetbar_props.start + assetbar_props.drag_x + ui_props.mouse_x + assetbar_props.width) <= region.width - assetbar_props.end:
                    assetbar_props.x_offset = min(region.width - assetbar_props.end - assetbar_props.start - 2*assetbar_props.drawoffset - ui_props.thumb_size, assetbar_props.drag_x + ui_props.mouse_x)
                assetbar_props.y_offset = min(region.height - assetbar_props.height, assetbar_props.drag_y - ui_props.mouse_y)

            if not (ui_props.dragging and ui_bgl.mouse_in_region(region, mx, my)) and not \
                    ui_bgl.mouse_in_asset_bar(context, mx, my):  #

                ui_props.dragging = False
                ui_props.has_hit = False
                ui_props.active_index = -3
                ui_props.draw_drag_image = False
                ui_props.draw_snapped_bounds = False
                ui_props.draw_tooltip = False
                return {'PASS_THROUGH'}

            if not ui_props.dragging:
                if assets != None and assetbar_props.wcount * assetbar_props.hcount > len(assets) and ui_props.scrolloffset > 0:
                    ui_props.scrolloffset = 0

                asset_search_index = ui_bgl.get_asset_under_mouse(context, mx, my)
                ui_props.active_index = asset_search_index
                if asset_search_index > -1:
                    ui_props.draw_tooltip = True
                else:
                    ui_props.draw_tooltip = False

                if mx > assetbar_props.x + assetbar_props.width - 50 and len(assets) - ui_props.scrolloffset > (assetbar_props.wcount * assetbar_props.hcount) + 1:
                    ui_props.active_index = -1
                    return {'RUNNING_MODAL'}

                if mx < assetbar_props.x + 50 and ui_props.scrolloffset > 0:
                    ui_props.active_index = -2
                    return {'RUNNING_MODAL'}

            else:
                context.window.cursor_set("NONE")
                if ui_props.dragging and ui_bgl.mouse_in_region(region, mx, my):
                    ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = ui_bgl.mouse_raycast(
                        context, mx, my)
                    # MODELS can be dragged on scene floor
                    if not ui_props.has_hit and ui_props.asset_type == 'MODEL':
                        ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = ui_bgl.floor_raycast(
                            context, mx, my)
                active_mod = assets[ui_props.active_index]
                if ui_props.has_hit and ui_props.asset_type == 'MODEL' and not (active_mod['patreon'] and active_mod['locked']):
                    # this condition is here to fix a bug for a scene submitted by a user, so this situation shouldn't
                    # happen anymore, but there might exists scenes which have this problem for some reason.
                    if ui_props.active_index < len(assets) and ui_props.active_index > -1:
                        ui_props.draw_snapped_bounds = True
                        ui_props.snapped_bbox_min = Vector(active_mod['bbox_min'])
                        ui_props.snapped_bbox_max = Vector(active_mod['bbox_max'])
                else:
                    ui_props.draw_snapped_bounds = False
                    ui_props.draw_drag_image = True
            return {'RUNNING_MODAL'}

        if event.type == 'RIGHTMOUSE':
            region = self.region
            mx = event.mouse_x - region.x
            my = event.mouse_y - region.y

            if event.value == 'PRESS' and ui_bgl.mouse_in_asset_bar(context, mx, my):
                #TODO: Implement context menu
                #bpy.ops.wm.call_menu(name='OBJECT_MT_LOL_asset_menu')
                return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE':
            region = self.region
            mx = event.mouse_x - region.x
            my = event.mouse_y - region.y

            ui_props = context.scene.luxcoreOL.ui
            if event.value == 'PRESS':
                if (mx - assetbar_props.x_offset-assetbar_props.start - 1) <= 2 and \
                        (mx - assetbar_props.x_offset-assetbar_props.start - 1) >= 0:
                    assetbar_props.resize_x_left = True
                    context.window.cursor_set("MOVE_X")
                    assetbar_props.resize_xy = assetbar_props.x_offset - mx
                    assetbar_props.resize_wh = assetbar_props.x_offset + assetbar_props.width
                    return {'RUNNING_MODAL'}

                elif(mx - assetbar_props.x_offset - assetbar_props.start - assetbar_props.width + 1 <= 0) and \
                        (mx - assetbar_props.x_offset - assetbar_props.start - assetbar_props.width + 1) >= -2:
                    assetbar_props.resize_x_right = True
                    assetbar_props.resize_wh = assetbar_props.width - mx
                    context.window.cursor_set("MOVE_X")
                    return {'RUNNING_MODAL'}

                elif (region.height - assetbar_props.y_offset - my - 1) >= 0 and \
                        (region.height - assetbar_props.y_offset - my - 1) <= 2:
                    assetbar_props.resize_y_top = True
                    context.window.cursor_set("MOVE_Y")
                    assetbar_props.resize_xy = assetbar_props.y_offset + my
                    assetbar_props.resize_wh = region.height - assetbar_props.y_offset - assetbar_props.height
                    return {'RUNNING_MODAL'}

                elif(region.height - assetbar_props.y_offset - my - assetbar_props.height + 1) <= 0 and \
                        (region.height - assetbar_props.y_offset - my - assetbar_props.height + 1) >= -2:
                    assetbar_props.resize_y_down = True
                    context.window.cursor_set("MOVE_Y")
                    assetbar_props.resize_wh = assetbar_props.height + my
                    return {'RUNNING_MODAL'}

                elif ui_props.active_index > -1:
                    if ui_props.asset_type == 'MODEL' or ui_props.asset_type == 'MATERIAL':
                        ui_props.drag_init = True
                        context.window.cursor_set("NONE")
                        ui_props.draw_tooltip = False
                        ui_props.drag_length = 0

            if not ui_props.dragging and not ui_bgl.mouse_in_asset_bar(context, mx, my) and \
                not assetbar_props.resize_x_left and not assetbar_props.resize_x_right and  \
                not assetbar_props.resize_y_top and not assetbar_props.resize_y_down:
                return {'PASS_THROUGH'}

            if event.value == 'RELEASE':  # Confirm
                if assetbar_props.resize_x_left or assetbar_props.resize_x_right or \
                        assetbar_props.resize_y_top or assetbar_props.resize_y_down:
                    assetbar_props.resize_x_left = False
                    assetbar_props.resize_x_right = False

                    assetbar_props.resize_y_top = False
                    assetbar_props.resize_y_down = False
                    return {'RUNNING_MODAL'}

                ui_props.drag_init = False

                # scroll by a whole page
                if ui_bgl.mouse_in_asset_bar(context, mx, my):
                    if mx > assetbar_props.x + assetbar_props.width - 50 and len(
                            assets) - ui_props.scrolloffset > assetbar_props.wcount * assetbar_props.hcount:
                        ui_props.scrolloffset = min(
                            ui_props.scrolloffset + (assetbar_props.wcount * assetbar_props.hcount),
                            len(assets) - assetbar_props.wcount * assetbar_props.hcount)
                        return {'RUNNING_MODAL'}
                    if mx < assetbar_props.x + 50 and ui_props.scrolloffset > 0:
                        ui_props.scrolloffset = max(0, ui_props.scrolloffset - assetbar_props.wcount * assetbar_props.hcount)
                        return {'RUNNING_MODAL'}

                # Drag-drop interaction
                if ui_props.dragging and ui_bgl.mouse_in_region(region, mx, my):
                    asset_search_index = ui_props.active_index
                    if assets[ui_props.active_index]['patreon'] and assets[ui_props.active_index]['locked']:
                        ui_props.dragging = False
                        ui_props.draw_snapped_bounds = False
                        ui_props.active_index = -3
                        import webbrowser
                        #webbrowser.open('https://blendermarket.com/creators/draviastudio')
                        webbrowser.open('https://www.cgtrader.com/draviastudio')

                        return {'RUNNING_MODAL'}

                    # raycast here
                    ui_props.active_index = -3

                    if ui_props.asset_type == 'MODEL':
                        ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = ui_bgl.mouse_raycast(
                            context, mx, my)

                        # MODELS can be dragged on scene floor
                        if not ui_props.has_hit:
                            ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = ui_bgl.floor_raycast(
                                context, mx, my)

                        if not ui_props.has_hit:
                            return {'RUNNING_MODAL'}

                        target_object = ''
                        if object is not None:
                            target_object = object.name
                        target_slot = ''

                    #TODO:_Implement Material drop
                    if ui_props.asset_type == 'MATERIAL':
                        ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = ui_bgl.mouse_raycast(
                            context, mx, my)

                    #     if not ui_props.has_hit:
                    #         # this is last attempt to get object under mouse - for curves and other objects than mesh.
                    #         ui_props.dragging = False
                    #         sel = utils.selection_get()
                    #         bpy.ops.view3d.select(location=(event.mouse_region_x, event.mouse_region_y))
                    #         sel1 = utils.selection_get()
                    #         if sel[0] != sel1[0] and sel1[0].type != 'MESH':
                    #             object = sel1[0]
                    #             target_slot = sel1[0].active_material_index
                    #             ui_props.has_hit = True
                    #         utils.selection_set(sel)
                    #
                        if not ui_props.has_hit:
                            return {'RUNNING_MODAL'}

                        else:
                            # first, test if object can have material applied.
                            #TODO: add other types here if droppable.
                            if object is not None and not object.is_library_indirect and object.type == 'MESH':
                                target_object = object.name
                                # create final mesh to extract correct material slot
                                depsgraph = context.evaluated_depsgraph_get()
                                object_eval = object.evaluated_get(depsgraph)
                                temp_mesh = object_eval.to_mesh()
                                target_slot = temp_mesh.polygons[face_index].material_index
                                object_eval.to_mesh_clear()
                            else:
                                self.report({'WARNING'}, "Invalid or library object as input:")
                                target_object = ''
                                target_slot = ''

                # Click interaction
                else:
                    asset_search_index = ui_bgl.get_asset_under_mouse(context, mx, my)
                    if assets[ui_props.active_index]['patreon'] and assets[ui_props.active_index]['locked']:
                        import webbrowser
                        #webbrowser.open('https://blendermarket.com/creators/draviastudio')
                        webbrowser.open('https://www.cgtrader.com/draviastudio')
                        return {'RUNNING_MODAL'}

                    if ui_props.asset_type in ('MATERIAL',
                                               'MODEL'):  # this was meant for particles, commenting for now or ui_props.asset_type == 'MODEL':
                        ao = bpy.context.active_object
                        if ao != None and not ao.is_library_indirect:
                            target_object = context.active_object.name
                            target_slot = context.active_object.active_material_index
                        else:
                            target_object = ''
                            target_slot = ''

                if asset_search_index == -3:
                    return {'RUNNING_MODAL'}

                if asset_search_index > -3:
                    if ui_props.has_hit and ui_props.dragging:
                        loc = ui_props.snapped_location
                        rotation = ui_props.snapped_rotation
                    else:
                        loc = scene.cursor.location
                        rotation = scene.cursor.rotation_euler

                    utils.load_asset(context, assets[asset_search_index], loc, rotation, target_object, target_slot)
                    ui_props.dragging = False
                    return {'RUNNING_MODAL'}
            else:
                return {'RUNNING_MODAL'}

        if event.type == 'MIDDLEMOUSE':
            region = self.region
            mx = event.mouse_x - region.x
            my = event.mouse_y - region.y
            ui_props = context.scene.luxcoreOL.ui
            assetbar_props = ui_props.assetbar

            if ui_bgl.mouse_in_asset_bar(context, mx, my):
                if event.value == 'PRESS':
                    assetbar_props.drag_init = True
                    assetbar_props.drag_x = assetbar_props.x_offset - mx
                    assetbar_props.drag_y = assetbar_props.y_offset + my
                    context.window.cursor_set("HAND")

                elif event.value == 'RELEASE':
                    assetbar_props.drag_init = False
                    assetbar_props.dragging = False

                return {'RUNNING_MODAL'}
            else:
                assetbar_props.drag_init = False
                assetbar_props.dragging = False

        return {'PASS_THROUGH'}


class LOLAssetKillDownloadOperator(bpy.types.Operator):
    """Kill a download"""
    bl_idname = "scene.luxcore_ol_download_kill"
    bl_label = "LuxCore Online Library Kill Asset Download"
    bl_options = {'REGISTER', 'INTERNAL'}

    thread_index: IntProperty(name="Thread index", description='index of the thread to kill', default=-1)

    def execute(self, context):
        td = utils.download_threads[self.thread_index]
        utils.download_threads.remove(td)
        scene = bpy.context.scene
        assets = utils.get_search_props(context)

        asset = td[1]
        for a in assets:
            if a['hash'] == asset['hash']:
                a['downloaded'] = 0.0
                break

        td[0].stop()

        for area in bpy.data.window_managers['WinMan'].windows[0].screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}