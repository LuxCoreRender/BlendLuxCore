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
from os.path import basename, dirname
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
    if not utils.guard_from_crash():
        return

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
        #draw_infobox(self, context)
        draw_callback_2d_search(self, context)


def draw_callback_2d_progress(self, context):
    green = (.2, 1, .2, .3)
    offset = 0
    row_height = 35

    scene = context.scene
    ui_props = scene.luxcoreOL.ui
    assets = scene.luxcoreOL['assets']
    if scene.luxcoreOL.on_search:
        assets = [asset for asset in scene.luxcoreOL['assets'] if asset['category'] == scene.luxcoreOL.search_category]

    # x = ui_props.reports_x
    # y = ui_props.reports_y
    index = 0
    for threaddata in utils.download_threads:
        tcom = threaddata[2]

        if tcom.passargs['thumbnail']:
            continue

        asset_data = threaddata[1]

        iname = asset_data['thumbnail']
        img = bpy.data.images.get(iname)
        if img is None:
            img = utils.get_thumbnail('thumbnail_notready.jpg')


        if tcom.passargs.get('downloaders'):
            for d in tcom.passargs['downloaders']:

                loc = view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d,
                                                            d['location'])
                if loc is not None:
                    ui_bgl.draw_image(loc[0], loc[1], 50, 50, img, 0.5)
        # else:
        #     ui_bgl.draw_progress(x, y - index * 30, text='downloading %s' % asset_data['name'],
        #                   percent=tcom.progress)
        #     index += 1
    # for process in bg_blender.bg_processes:
    #     tcom = process[1]
    #     draw_progress(x, y - index * 30, '%s' % tcom.lasttext,
    #                   tcom.progress)
    #     index += 1
    # global reports
    # for report in reports:
    #     report.draw(x, y - index * 30)
    #     index += 1
    #     report.fade()


def draw_callback_3d_progress(self, context):
    # 'star trek' mode gets here, blocked by now ;)
    if not utils.guard_from_crash():
        return

    for threaddata in utils.download_threads:
        tcom = threaddata[2]
        if tcom.passargs['thumbnail']:
            continue

        asset_data = threaddata[1]
        bbox_min = Vector(asset_data["bbox_min"])
        bbox_max = Vector(asset_data["bbox_max"])
        bbox_center = 0.5 * Vector((bbox_max[0] + bbox_min[0], bbox_max[1] + bbox_min[1], 0.0))

        if tcom.passargs.get('downloaders'):
            for d in tcom.passargs['downloaders']:
                ui_bgl.draw_bbox(d['location'], d['rotation'], bbox_min-bbox_center, bbox_max-bbox_center,
                               progress=tcom.progress)


def draw_callback_3d(self, context):
    ''' Draw snapped bbox while dragging'''
    if not utils.guard_from_crash():
        return

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
    assets = scene.luxcoreOL['assets']

    if scene.luxcoreOL.on_search:
        assets = [asset for asset in scene.luxcoreOL['assets'] if asset['category'] == scene.luxcoreOL.search_category]

    name = basename(dirname(dirname(dirname(__file__))))
    user_preferences = context.preferences.addons[name].preferences

    region = self.region
    hcolor = (1, 1, 1, .07)
    grey = (hcolor[0] * .8, hcolor[1] * .8, hcolor[2] * .8, .5)
    white = (1, 1, 1, 0.2)
    green = (.2, 1, .2, .7)
    highlight = (1, 1, 1, .3)

    # background of asset bar

    if not ui_props.dragging:
        if len(assets) == 0:
            return

        h_draw = min(ui_props.hcount, math.ceil(len(assets) / ui_props.wcount))

        if ui_props.wcount > len(assets):
            bar_width = len(assets) * (ui_props.thumb_size + ui_props.margin) + ui_props.margin
        else:
            bar_width = ui_props.bar_width

        row_height = ui_props.thumb_size + ui_props.margin
        ui_bgl.draw_rect(ui_props.bar_x, ui_props.bar_y - ui_props.bar_height, bar_width,
                         ui_props.bar_height, hcolor)

        if len(assets) != 0:
            if ui_props.scrolloffset > 0 or ui_props.wcount * ui_props.hcount < len(assets):
                ui_props.drawoffset = 35
            else:
                ui_props.drawoffset = 0

            # Draw scroll arrows
            if ui_props.wcount * ui_props.hcount < len(assets):
                arrow_y = ui_props.bar_y - int((ui_props.bar_height + ui_props.thumb_size) / 2) + ui_props.margin
                if ui_props.scrolloffset > 0:

                    if ui_props.active_index == -2:
                        ui_bgl.draw_rect(ui_props.bar_x, ui_props.bar_y - ui_props.bar_height, 25,
                                         ui_props.bar_height, highlight)

                    ui_bgl.draw_image(ui_props.bar_x, arrow_y, 25,
                                      ui_props.thumb_size, utils.get_thumbnail('arrow_left.png'), 1)

                if len(assets) - ui_props.scrolloffset > (ui_props.wcount * ui_props.hcount) + 1:
                    if ui_props.active_index == -1:
                        ui_bgl.draw_rect(ui_props.bar_x + ui_props.bar_width - 25,
                                         ui_props.bar_y - ui_props.bar_height, 25,
                                         ui_props.bar_height,
                                         highlight)

                    ui_bgl.draw_image(ui_props.bar_x + ui_props.bar_width - 25, arrow_y, 25,
                                      ui_props.thumb_size, utils.get_thumbnail('arrow_right.png'), 1)

            # Draw asset thumbnails
            for b in range(0, h_draw):
                w_draw = min(ui_props.wcount, len(assets) - b * ui_props.wcount - ui_props.scrolloffset)

                y = ui_props.bar_y - (b + 1) * (row_height)
                for a in range(0, w_draw):
                    x = ui_props.bar_x + a * (
                            ui_props.margin + ui_props.thumb_size) + ui_props.margin + ui_props.drawoffset

                    index = a + ui_props.scrolloffset + b * ui_props.wcount
                    iname = assets[index]['thumbnail']
                    img = bpy.data.images.get(iname)

                    if img is None or img.size[0] == 0:
                        img = utils.get_thumbnail('thumbnail_notready.jpg')

                    w = int(ui_props.thumb_size * img.size[0] / max(img.size[0], img.size[1]))
                    h = int(ui_props.thumb_size * img.size[1] / max(img.size[0], img.size[1]))
                    crop = (0, 0, 1, 1)
                    if img.size[0] > img.size[1]:
                        offset = (1 - img.size[1] / img.size[0]) / 2
                        crop = (offset, 0, 1 - offset, 1)
                    if img is not None:
                        ui_bgl.draw_image(x, y, w, w, img, 1, crop=crop)
                        if index == ui_props.active_index:
                            ui_bgl.draw_rect(x - ui_props.highlight_margin, y - ui_props.highlight_margin,
                                             w + 2 * ui_props.highlight_margin, w + 2 * ui_props.highlight_margin,
                                             highlight)
                    else:
                        ui_bgl.draw_rect(x, y, w, h, white)

    # TODO: Transfer to LOL

    #                 result = search_results[index]
    #                 if result['downloaded'] > 0:
    #                     ui_bgl.draw_rect(x, y - 2, int(w * result['downloaded'] / 100.0), 2, green)
    #
    #                 if (result.get('can_download', True)) == 0:
    #                     img = utils.get_thumbnail('locked.png')
    #                     ui_bgl.draw_image(x + 2, y + 2, 24, 24, img, 1)
    #
    #                 v_icon = verification_icons[result.get('verification_status', 'validated')]
    #                 if v_icon is not None:
    #                     img = utils.get_thumbnail(v_icon)
    #                     ui_bgl.draw_image(x + ui_props.thumb_size - 26, y + 2, 24, 24, img, 1)

    # TODO: Transfer to LOL

    #     s = bpy.context.scene
    #     props = utils.get_search_props()
    #     # if props.report != '' and props.is_searching or props.search_error:
    #     #     ui_bgl.draw_text(props.report, ui_props.bar_x,
    #     #                      ui_props.bar_y - 15 - ui_props.margin - ui_props.bar_height, 15)
    #
    #     props = s.blenderkitUI
    #     if ui_props.draw_tooltip:
    #         # TODO move this lazy loading into a function and don't duplicate through the code
    #         iname = utils.previmg_name(ui_props.active_index, fullsize=True)
    #
    #         directory = paths.get_temp_dir('%s_search' % mappingdict[props.asset_type])
    #         sr = scene.get('search results')
    #         if sr != None and -1 < ui_props.active_index < len(sr):
    #             r = sr[ui_props.active_index]
    #             tpath = os.path.join(directory, r['thumbnail'])
    #
    #             img = bpy.data.images.get(iname)
    #             if img == None or img.filepath != tpath:
    #                 # TODO replace it with a function
    #                 if os.path.exists(tpath):
    #
    #                     if img is None:
    #                         img = bpy.data.images.load(tpath)
    #                         img.name = iname
    #                     else:
    #                         if img.filepath != tpath:
    #                             # todo replace imgs reloads with a method that forces unpack for thumbs.
    #                             if img.packed_file is not None:
    #                                 img.unpack(method='USE_ORIGINAL')
    #                             img.filepath = tpath
    #                             img.reload()
    #                             img.name = iname
    #                 else:
    #                     iname = utils.previmg_name(ui_props.active_index)
    #                     img = bpy.data.images.get(iname)
    #                 img.colorspace_settings.name = 'Linear'
    #
    #             gimg = None
    #             atip = ''
    #             if bpy.context.window_manager.get('bkit authors') is not None:
    #                 a = bpy.context.window_manager['bkit authors'].get(r['author_id'])
    #                 if a is not None and a != '':
    #                     if a.get('gravatarImg') is not None:
    #                         gimg = utils.get_hidden_image(a['gravatarImg'], a['gravatarHash'])
    #                     atip = a['tooltip']
    #
    #             draw_tooltip(ui_props.mouse_x, ui_props.mouse_y, text=ui_props.tooltip, author=atip, img=img,
    #                          gravatar=gimg)


    # Scroll assets with mouse wheel
    if ui_props.dragging and (
            ui_props.draw_drag_image or ui_props.draw_snapped_bounds) and ui_props.active_index > -1:
        iname = assets[ui_props.active_index]['thumbnail']
        img = bpy.data.images.get(iname)
        if img is None:
            img = utils.get_thumbnail('thumbnail_notready.jpg')

        linelength = 35
        ui_bgl.draw_image(ui_props.mouse_x + linelength, ui_props.mouse_y - linelength - ui_props.thumb_size,
                          ui_props.thumb_size, ui_props.thumb_size, img, 1)
        ui_bgl.draw_line2d(ui_props.mouse_x, ui_props.mouse_y, ui_props.mouse_x + linelength,
                           ui_props.mouse_y - linelength, 2, white)


def draw_infobox(self, context):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui

    #TODO: Implement

    # rating_possible, rated, asset, asset_data = is_rating_possible()

    # if rating_possible:  # (not rated or ui_props.rating_menu_on):
    #     bkit_ratings = asset.bkit_ratings
    #     bgcol = bpy.context.preferences.themes[0].user_interface.wcol_tooltip.inner
    #     textcol = (1, 1, 1, 1)
    #
    #     r = bpy.context.region
    #     font_size = int(ui.rating_ui_scale * 20)
    #
    #     if ui.rating_button_on:
    #         img = utils.get_thumbnail('star_white.png')
    #
    #         ui_bgl.draw_image(ui.rating_x,
    #                           ui.rating_y - ui.rating_button_width,
    #                           ui.rating_button_width,
    #                           ui.rating_button_width,
    #                           img, 1)
    #
    #         # if ui_props.asset_type != 'BRUSH':
    #         #     thumbnail_image = props.thumbnail
    #         # else:
    #         #     b = utils.get_active_brush()
    #         #     thumbnail_image = b.icon_filepath
    #
    #         directory = paths.get_temp_dir('%s_search' % asset_data['asset_type'])
    #         tpath = os.path.join(directory, asset_data['thumbnail_small'])
    #
    #         img = utils.get_hidden_image(tpath, 'rating_preview')
    #         ui_bgl.draw_image(ui.rating_x + ui.rating_button_width,
    #                           ui.rating_y - ui.rating_button_width,
    #                           ui.rating_button_width,
    #                           ui.rating_button_width,
    #                           img, 1)
    #         # ui_bgl.draw_text( 'rate asset %s' % asset_data['name'],r.width - rating_button_width + margin, margin, font_size)
    #         return
    #
    #     ui_bgl.draw_rect(ui.rating_x,
    #                      ui.rating_y - ui.rating_ui_height - 2 * ui.margin - font_size,
    #                      ui.rating_ui_width + ui.margin,
    #                      ui.rating_ui_height + 2 * ui.margin + font_size,
    #                      bgcol)
    #     if asset_data['asset_type'] == 'model':
    #         ui_img_name = 'rating_ui.png'
    #     else:
    #         ui_img_name = 'rating_ui_empty.png'
    #         text = 'Try to estimate how many hours it would take for a professional artist to create this asset:'
    #         tx = ui.rating_x + ui.workhours_bar_x
    #         # draw_text_block(x=tx, y=ui.rating_y, width=80, font_size=20, line_height=15, text=text, color=colors.TEXT)
    #
    #     img = utils.get_thumbnail(ui_img_name)
    #     ui_bgl.draw_image(ui.rating_x,
    #                       ui.rating_y - ui.rating_ui_height - 2 * ui.margin,
    #                       ui.rating_ui_width,
    #                       ui.rating_ui_height,
    #                       img, 1)
    #     img = utils.get_thumbnail('star_white.png')
    #
    #     quality = bkit_ratings.rating_quality
    #     work_hours = bkit_ratings.rating_work_hours
    #
    #     for a in range(0, quality):
    #         ui_bgl.draw_image(ui.rating_x + ui.quality_stars_x + a * ui.star_size,
    #                           ui.rating_y - ui.rating_ui_height + ui.quality_stars_y,
    #                           ui.star_size,
    #                           ui.star_size,
    #                           img, 1)
    #
    #     img = utils.get_thumbnail('bar_slider.png')
    #     # for a in range(0,11):
    #     if work_hours > 0.2:
    #         if asset_data['asset_type'] == 'model':
    #             complexity = math.log2(work_hours) + 2  # real complexity
    #             complexity = (1. / 9.) * (complexity - 1) * ui.workhours_bar_x_max
    #         else:
    #             complexity = work_hours / 5 * ui.workhours_bar_x_max
    #         ui_bgl.draw_image(
    #             ui.rating_x + ui.workhours_bar_x + int(
    #                 complexity),
    #             ui.rating_y - ui.rating_ui_height + ui.workhours_bar_y,
    #             ui.workhours_bar_slider_size,
    #             ui.workhours_bar_slider_size, img, 1)
    #         ui_bgl.draw_text(
    #             str(round(work_hours, 1)),
    #             ui.rating_x + ui.workhours_bar_x - 50,
    #             ui.rating_y - ui.rating_ui_height + ui.workhours_bar_y + 10, font_size)
    #     # (0.5,1,2,4,8,16,32,64,128,256)
    #     # ratings have to be different for models and brushes+materials.
    #
    #     scalevalues, xs = get_rating_scalevalues(asset_data['asset_type'])
    #     for v, x in zip(scalevalues, xs):
    #         ui_bgl.draw_rect(ui.rating_x + ui.workhours_bar_x + int(
    #             x * ui.workhours_bar_x_max) - 1 + ui.workhours_bar_slider_size / 2,
    #                          ui.rating_y - ui.rating_ui_height + ui.workhours_bar_y,
    #                          2,
    #                          5,
    #                          textcol)
    #         ui_bgl.draw_text(str(v),
    #                          ui.rating_x + ui.workhours_bar_x + int(
    #                              x * ui.workhours_bar_x_max),
    #                          ui.rating_y - ui.rating_ui_height + ui.workhours_bar_y - 30,
    #                          font_size)
    #     if work_hours > 0.2 and quality > 0.2:
    #         text = 'Thanks for rating asset %s' % asset_data['name']
    #     else:
    #         text = 'Rate asset %s.' % asset_data['name']
    #     ui_bgl.draw_text(text,
    #                      ui.rating_x,
    #                      ui.rating_y - ui.margin - font_size,
    #                      font_size)


def draw_tooltip(x, y, text='', author='', img=None, gravatar=None):
    region = bpy.context.region
    scale = bpy.context.preferences.view.ui_scale

    ttipmargin = 5
    textmargin = 10

    font_height = int(12 * scale)
    line_height = int(15 * scale)
    nameline_height = int(23 * scale)

    lines = text.split('\n')
    alines = author.split('\n')
    ncolumns = 2
    # nlines = math.ceil((len(lines) - 1) / ncolumns)
    nlines = max(len(lines) - 1, len(alines))  # math.ceil((len(lines) - 1) / ncolumns)

    texth = line_height * nlines + nameline_height

    if max(img.size[0], img.size[1]) == 0:
        return;
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
    ui_bgl.draw_rect(x - ttipmargin,
                     y - 2 * ttipmargin - isizey,
                     isizex + ttipmargin * 2,
                     2 * ttipmargin + isizey,
                     bgcol)
    # main preview image
    ui_bgl.draw_image(x, y - isizey - ttipmargin, isizex, isizey, img, 1)

    # text overlay background
    ui_bgl.draw_rect(x - ttipmargin,
                     y - 2 * ttipmargin - isizey,
                     isizex + ttipmargin * 2,
                     2 * ttipmargin + texth,
                     bgcol1)
    # draw gravatar
    gsize = 40
    if gravatar is not None:
        # ui_bgl.draw_image(x + isizex - gsize - textmargin, y - isizey + texth - gsize - nameline_height - textmargin,
        #                   gsize, gsize, gravatar, 1)
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
    xtext += int(isizex / ncolumns)

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

        scene.luxcoreOL.search_category = ""
        scene.luxcoreOL.on_search = self.do_search

        assets = scene.luxcoreOL.get('assets')

        if not ui_props.thumbnails_loaded:
            utils.load_previews(context, assets)
            ui_props.thumbnails_loaded = True


        ui_props.scrolloffset = 0

        if scene.luxcoreOL.on_search:
            assets = [asset for asset in scene.luxcoreOL['assets'] if asset['category'] == self.category]
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

        global active_window, active_area, active_region
        active_window = self.window
        active_area = self.area
        active_region = self.region

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
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d_progress, 'WINDOW')

        except:
            pass

        self.area.tag_redraw()

    def modal(self, context, event):
        scene = context.scene
        ui_props = context.scene.luxcoreOL.ui

        user_preferences = get_addon_preferences(context)
        assets = scene.luxcoreOL.get('assets')

        if scene.luxcoreOL.on_search:
            assets = [asset for asset in scene.luxcoreOL['assets'] if asset['category'] == scene.luxcoreOL.search_category]

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

            if ui_props.dragging and not ui_bgl.mouse_in_asset_bar(context, mx, my):  # and my < r.height - ui_props.bar_height \
                # and mx > 0 and mx < r.width and my > 0:
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

            if (event.type == 'WHEELDOWNMOUSE') and len(assets) - ui_props.scrolloffset > (
                    ui_props.wcount * ui_props.hcount):
                if ui_props.hcount > 1:
                    ui_props.scrolloffset += ui_props.wcount
                else:
                    ui_props.scrolloffset += 1
                if len(assets) - ui_props.scrolloffset < (ui_props.wcount * ui_props.hcount):
                    ui_props.scrolloffset = len(assets) - (ui_props.wcount * ui_props.hcount)

            if event.type == 'WHEELUPMOUSE' and ui_props.scrolloffset > 0:
                if ui_props.hcount > 1:
                    ui_props.scrolloffset -= ui_props.wcount
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

            #if ui_props.dragging_rating or ui_props.rating_menu_on:
            #    res = interact_rating(region, mx, my, event)
            #    if res == True:
            #        return {'RUNNING_MODAL'}

            if ui_props.drag_init:
                ui_props.drag_length += 1
                if ui_props.drag_length > 0:
                    ui_props.dragging = True
                    ui_props.drag_init = False

            if not (ui_props.dragging and ui_bgl.mouse_in_region(region, mx, my)) and not \
                    ui_bgl.mouse_in_asset_bar(context, mx, my):  #

                ui_props.dragging = False
                ui_props.has_hit = False
                ui_props.active_index = -3
                ui_props.draw_drag_image = False
                ui_props.draw_snapped_bounds = False
                ui_props.draw_tooltip = False
                bpy.context.window.cursor_set("DEFAULT")
                return {'PASS_THROUGH'}


            if not ui_props.dragging:
                bpy.context.window.cursor_set("DEFAULT")

                if assets != None and ui_props.wcount * ui_props.hcount > len(assets) and ui_props.scrolloffset > 0:
                    ui_props.scrolloffset = 0

                asset_search_index = ui_bgl.get_asset_under_mouse(context, mx, my)
                ui_props.active_index = asset_search_index
                if asset_search_index > -1:

                    asset_data = assets[asset_search_index]
                    ui_props.draw_tooltip = True

                    # ui_props.tooltip = asset_data['tooltip']
                    # bpy.ops.wm.call_menu(name='OBJECT_MT_blenderkit_asset_menu')

                else:
                    ui_props.draw_tooltip = False

                #if mx > ui_props.bar_x + ui_props.bar_width - 50 and search_results_orig[
                #    'count'] - ui_props.scrolloffset > (ui_props.wcount * ui_props.hcount) + 1:
                #    ui_props.active_index = -1
                #    return {'RUNNING_MODAL'}

                if mx < ui_props.bar_x + 50 and ui_props.scrolloffset > 0:
                    ui_props.active_index = -2
                    return {'RUNNING_MODAL'}

            else:
                result = False
                if ui_props.dragging and ui_bgl.mouse_in_region(region, mx, my):
                    ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = ui_bgl.mouse_raycast(
                        context, mx, my)
                    # MODELS can be dragged on scene floor
                    if not ui_props.has_hit and ui_props.asset_type == 'MODEL':
                        ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = ui_bgl.floor_raycast(
                            context, mx, my)
                if ui_props.has_hit and ui_props.asset_type == 'MODEL':
                    # this condition is here to fix a bug for a scene submitted by a user, so this situation shouldn't
                    # happen anymore, but there might exists scenes which have this problem for some reason.
                    if ui_props.active_index < len(assets) and ui_props.active_index > -1:
                        ui_props.draw_snapped_bounds = True
                        active_mod = assets[ui_props.active_index]
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
                #bpy.ops.wm.call_menu(name='OBJECT_MT_LOL_asset_menu')
                return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE':
            region = self.region
            mx = event.mouse_x - region.x
            my = event.mouse_y - region.y

            ui_props = context.scene.luxcoreOL.ui
            if event.value == 'PRESS' and ui_props.active_index > -1:
                if ui_props.asset_type == 'MODEL' or ui_props.asset_type == 'MATERIAL':
                    # check if asset is locked and let the user know in that case
                    asset_search_index = ui_props.active_index
                    asset_data = assets[asset_search_index]
                    # if not asset_data['can_download']:
                    #     message = 'Asset locked. Find out how to unlock Everything and ...'
                    #     link_text = 'support all BlenderKit artists.'
                    #     url = paths.get_bkit_url() + '/get-blenderkit/' + asset_data['id'] + '/?from_addon'
                    #     bpy.ops.wm.blenderkit_url_dialog('INVOKE_REGION_WIN', url=url, message=message,
                    #                                      link_text=link_text)
                    #     return {'RUNNING_MODAL'}
                    # go on with drag init
                    ui_props.drag_init = True
                    context.window.cursor_set("NONE")
                    ui_props.draw_tooltip = False
                    ui_props.drag_length = 0

            if not ui_props.dragging and not ui_bgl.mouse_in_asset_bar(context, mx, my):
                return {'PASS_THROUGH'}

            if event.value == 'RELEASE':  # Confirm
                ui_props.drag_init = False

                # scroll by a whole page
                if mx > ui_props.bar_x + ui_props.bar_width - 50 and len(
                        assets) - ui_props.scrolloffset > ui_props.wcount * ui_props.hcount:
                    ui_props.scrolloffset = min(
                        ui_props.scrolloffset + (ui_props.wcount * ui_props.hcount),
                        len(assets) - ui_props.wcount * ui_props.hcount)
                    return {'RUNNING_MODAL'}
                if mx < ui_props.bar_x + 50 and ui_props.scrolloffset > 0:
                    ui_props.scrolloffset = max(0, ui_props.scrolloffset - ui_props.wcount * ui_props.hcount)
                    return {'RUNNING_MODAL'}

                # Drag-drop interaction
                if ui_props.dragging and ui_bgl.mouse_in_region(region, mx, my):
                    asset_search_index = ui_props.active_index
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
                    # if ui_props.asset_type == 'MATERIAL':
                    #     ui_props.has_hit, ui_props.snapped_location, ui_props.snapped_normal, ui_props.snapped_rotation, face_index, object, matrix = mouse_raycast(
                    #         context, mx, my)
                    #
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
                    #     if not ui_props.has_hit:
                    #         return {'RUNNING_MODAL'}
                    #
                    #     else:
                    #         # first, test if object can have material applied.
                    #         # TODO add other types here if droppable.
                    #         if object is not None and not object.is_library_indirect and object.type == 'MESH':
                    #             target_object = object.name
                    #             # create final mesh to extract correct material slot
                    #             depsgraph = bpy.context.evaluated_depsgraph_get()
                    #             object_eval = object.evaluated_get(depsgraph)
                    #             temp_mesh = object_eval.to_mesh()
                    #             target_slot = temp_mesh.polygons[face_index].material_index
                    #             object_eval.to_mesh_clear()
                    #         else:
                    #             self.report({'WARNING'}, "Invalid or library object as input:")
                    #             target_object = ''
                    #             target_slot = ''

                # Click interaction
                else:
                    asset_search_index = ui_bgl.get_asset_under_mouse(context, mx, my)
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

                    utils.load_asset(context, assets[asset_search_index], loc, rotation)
                    ui_props.dragging = False
                    return {'RUNNING_MODAL'}
            else:
                return {'RUNNING_MODAL'}

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
        td[0].stop()
        return {'FINISHED'}