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

import blf
import bpy
import gpu
import math
import random
from mathutils import Vector
import mathutils

from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from ...utils import get_addon_preferences
from ...utils.lol import utils as utils


def draw_downloader(x, y, percent=0, img=None):
    if img is not None:
        draw_image(x, y, 50, 50, img, .5)
    draw_rect(x, y, 50, int(0.5 * percent), (.2, 1, .2, .3))
    draw_rect(x - 3, y - 3, 6, 6, (1, 0, 0, .3))


def draw_progress(x, y, text='', percent=None, color=(0, 1, 0, 1)):
    draw_rect(x, y, percent, 5, color)
    draw_text(text, x, y + 8, 16, color)


def draw_rect(x, y, width, height, color):
    gpu.state.blend_set('ALPHA')
    xmax = x + width
    ymax = y + height
    points = [[x, y],  # [x, y]
              [x, ymax],  # [x, y]
              [xmax, ymax],  # [x, y]
              [xmax, y],  # [x, y]
              ]
    indices = ((0, 1, 2), (2, 3, 0))

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": points}, indices=indices)

    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_line2d(x1, y1, x2, y2, width, color):
    coords = (
        (x1, y1), (x2, y2))

    indices = (
        (0, 1),)

    gpu.state.blend_set('ALPHA')
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_lines(vertices, indices, color):
    gpu.state.blend_set('ALPHA')
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')

def draw_rect_3d(coords, color):
    indices = [(0, 1, 2), (2, 3, 0)]
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_bbox(location, rotation, bbox_min, bbox_max, progress=None, color=(0, 1, 0, 1)):
    rotation = mathutils.Euler(rotation)

    smin = Vector(bbox_min)
    smax = Vector(bbox_max)
    v0 = Vector(smin)
    v1 = Vector((smax.x, smin.y, smin.z))
    v2 = Vector((smax.x, smax.y, smin.z))
    v3 = Vector((smin.x, smax.y, smin.z))
    v4 = Vector((smin.x, smin.y, smax.z))
    v5 = Vector((smax.x, smin.y, smax.z))
    v6 = Vector((smax.x, smax.y, smax.z))
    v7 = Vector((smin.x, smax.y, smax.z))

    arrowx = smin.x + (smax.x - smin.x) / 2
    arrowy = smin.y - (smax.x - smin.x) / 2
    v8 = Vector((arrowx, arrowy, smin.z))

    vertices = [v0, v1, v2, v3, v4, v5, v6, v7, v8]
    for v in vertices:
        v.rotate(rotation)
        v += Vector(location)

    lines = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5],
             [2, 6], [3, 7], [0, 8], [1, 8]]
    draw_lines(vertices, lines, color)
    if progress != None:
        color = (color[0], color[1], color[2], .2)
        progress = progress * .01
        vz0 = (v4 - v0) * progress + v0
        vz1 = (v5 - v1) * progress + v1
        vz2 = (v6 - v2) * progress + v2
        vz3 = (v7 - v3) * progress + v3
        rects = (
            (v0, v1, vz1, vz0),
            (v1, v2, vz2, vz1),
            (v2, v3, vz3, vz2),
            (v3, v0, vz0, vz3))
        for r in rects:
            draw_rect_3d(r, color)


def draw_image(x, y, width, height, image, transparency, crop=(0, 0, 1, 1)):
    coords = [
        (x, y), (x + width, y),
        (x, y + height), (x + width, y + height)]

    uvs = [(crop[0], crop[1]),
           (crop[2], crop[1]),
           (crop[0], crop[3]),
           (crop[2], crop[3]),
           ]

    indices = [(0, 1, 2), (2, 1, 3)]

    gpu.state.blend_set('ALPHA')
    shader = gpu.shader.from_builtin('IMAGE')
    batch = batch_for_shader(shader, 'TRIS',
                             {"pos": coords,
                              "texCoord": uvs},
                             indices=indices)

    texture = gpu.texture.from_image(image)

    shader.bind()
    shader.uniform_sampler("image", texture)
    batch.draw(shader)

    gpu.state.blend_set('NONE')


def draw_downloader(x, y, percent=0, img=None):
    if img is not None:
        draw_image(x, y, 50, 50, img, .5)
    draw_rect(x, y, 50, int(0.5 * percent), (.2, 1, .2, .3))
    draw_rect(x - 3, y - 3, 6, 6, (1, 0, 0, .3))


def draw_progress(x, y, text='', percent=None, color=(.2, 1, .2, .7)):
    draw_rect(x, y, percent, 5, color)
    draw_text(text, x, y + 8, 16, color)


def draw_text(text, x, y, size, color=(1, 1, 1, 0.5)):
    font_id = 0
    # bgl.glColor4f(*color)
    blf.color(font_id, color[0], color[1], color[2], color[3])
    blf.position(font_id, x, y, 0)
    blf.size(font_id, size)
    blf.draw(font_id, text)


def init_ui_size(context, area, region):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui
    assetbar_props = ui_props.assetbar

    # assets = utils.get_search_props(context)
    # if scene.luxcoreOL.on_search:
    #     assets = [asset for asset in utils.get_search_props(context) if asset['category'] == scene.luxcoreOL.search_category]

    user_preferences = get_addon_preferences(context)
    ui_scale = bpy.context.preferences.view.ui_scale

    assetbar_props.margin = math.floor(assetbar_props.bl_rna.properties['margin'].default * ui_scale)
    ui_props.thumb_size = math.floor(user_preferences.thumb_size * ui_scale)

    reg_multiplier = 1
    if not bpy.context.preferences.system.use_region_overlap:
        reg_multiplier = 0

    for r in area.regions:
        if r.type == 'TOOLS':
            assetbar_props.start = r.width * reg_multiplier
            assetbar_props.x = math.floor(r.width * reg_multiplier + assetbar_props.margin + assetbar_props.x_offset * ui_scale)
        elif r.type == 'UI':
            assetbar_props.end = math.floor(r.width * reg_multiplier + 100 * ui_scale)

    assetbar_props.width = region.width - assetbar_props.x - assetbar_props.end
    assetbar_props.wcount = math.floor(
        (assetbar_props.width - 2 * assetbar_props.drawoffset) / (ui_props.thumb_size + assetbar_props.margin))

    assetbar_props.hcount = 1
    assetbar_props.height = (ui_props.thumb_size + assetbar_props.margin) * assetbar_props.hcount + assetbar_props.margin
    assetbar_props.y = math.floor(region.height - assetbar_props.y_offset * ui_scale)

    ui_props.reports_y = assetbar_props.y - assetbar_props.height - 100
    ui_props.reports_x = assetbar_props.x

    ui_props.rating_x = assetbar_props.x
    ui_props.rating_y = assetbar_props.y - assetbar_props.height


def update_ui_size(context, area, region):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui
    assetbar_props = ui_props.assetbar

    assets = utils.get_search_props(context)

    if ui_props.local:
        assets = [asset for asset in assets if asset['local']]

    if ui_props.free_only:
        assets = [asset for asset in assets if not asset['locked']]

    if scene.luxcoreOL.on_search:
        assets = [asset for asset in assets if asset['category'] == scene.luxcoreOL.search_category]

    user_preferences = get_addon_preferences(context)

    ui_scale = bpy.context.preferences.view.ui_scale

    assetbar_props.margin = math.floor(assetbar_props.bl_rna.properties['margin'].default * ui_scale)

    reg_multiplier = 1
    if not bpy.context.preferences.system.use_region_overlap:
        reg_multiplier = 0

    for r in area.regions:
        if r.type == 'TOOLS':
            assetbar_props.start = r.width * reg_multiplier
            assetbar_props.x = math.floor(r.width * reg_multiplier + assetbar_props.margin + assetbar_props.x_offset * ui_scale)
        elif r.type == 'UI':
            assetbar_props.end = math.floor(r.width * reg_multiplier + 100 * ui_scale)

    if assetbar_props.height < ui_props.thumb_size + 2 * assetbar_props.margin:
        assetbar_props.height = ui_props.thumb_size + 2 * assetbar_props.margin

    if region.height - assetbar_props.y_offset - assetbar_props.height < 0:
        assetbar_props.y_offset = region.height - assetbar_props.height

    if assetbar_props.width < ui_props.thumb_size + 2*assetbar_props.margin + assetbar_props.drawoffset:
        assetbar_props.width = region.width - assetbar_props.end - assetbar_props.start

    if (assetbar_props.start + assetbar_props.x_offset + assetbar_props.width) > region.width - assetbar_props.end:
        assetbar_props.x_offset = region.width - assetbar_props.end - assetbar_props.width

        if (assetbar_props.start + assetbar_props.x_offset + assetbar_props.width) > region.width - assetbar_props.end:
            assetbar_props.width = region.width - assetbar_props.end - assetbar_props.start


    assetbar_props.y = math.floor(region.height - assetbar_props.y_offset * ui_scale)

    assetbar_props.wcount = math.floor(
        (assetbar_props.width - 2 * assetbar_props.drawoffset) / (ui_props.thumb_size + assetbar_props.margin))

    if assets != None and assetbar_props.wcount > 0:
        assetbar_props.hcount = math.floor(assetbar_props.height / (ui_props.thumb_size + 2*assetbar_props.margin))
    else:
        assetbar_props.hcount = 1


def get_largest_3dview():
    maxsurf = 0
    maxa = None
    maxw = None
    region = None
    for w in bpy.context.window_manager.windows:
        screen = w.screen
        for a in screen.areas:
            if a.type == 'VIEW_3D':
                asurf = a.width * a.height
                if asurf > maxsurf:
                    maxa = a
                    maxw = w
                    maxsurf = asurf

                    for r in a.regions:
                        if r.type == 'WINDOW':
                            region = r
    global active_area, active_window, active_region
    active_window = maxw
    active_area = maxa
    active_region = region
    return maxw, maxa, region


def mouse_in_area(mx, my, x, y, w, h):
    if x < mx < x + w and y < my < y + h:
        return True
    else:
        return False


def mouse_in_asset_bar(context, mx, my):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui
    assetbar_props = ui_props.assetbar

    if assetbar_props.y - assetbar_props.height < my < assetbar_props.y \
            and assetbar_props.x < mx < assetbar_props.x + assetbar_props.width:
        return True
    else:
        return False


def mouse_in_region(region, mx, my):
    if 0 < my < region.height and 0 < mx < region.width:
        return True
    else:
        return False


def get_asset_under_mouse(context, mousex, mousey):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui
    assetbar_props = ui_props.assetbar

    assets = utils.get_search_props(context)

    if ui_props.local:
        assets = [asset for asset in assets if asset['local']]

    if ui_props.free_only:
        assets = [asset for asset in assets if not asset['locked']]

    if scene.luxcoreOL.on_search:
        assets = [asset for asset in assets if asset['category'] == scene.luxcoreOL.search_category]

    if assets is not None:
        h_draw = min(assetbar_props.hcount, math.ceil(len(assets) / assetbar_props.wcount))
        for b in range(0, h_draw):
            w_draw = min(assetbar_props.wcount, len(assets) - b * assetbar_props.wcount - ui_props.scrolloffset)
            for a in range(0, w_draw):
                x = assetbar_props.x + a * (assetbar_props.margin + ui_props.thumb_size) + assetbar_props.margin + assetbar_props.drawoffset
                y = assetbar_props.y - assetbar_props.margin - (ui_props.thumb_size + assetbar_props.margin) * (b + 1)
                w = ui_props.thumb_size
                h = ui_props.thumb_size

                if x < mousex < x + w and y < mousey < y + h:
                    return a + assetbar_props.wcount * b + ui_props.scrolloffset
    return -3

def mouse_raycast(context, mx, my):
    r = context.region
    rv3d = context.region_data
    coord = mx, my

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(r, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(r, rv3d, coord)
    ray_target = ray_origin + (view_vector * 1000000000)

    vec = ray_target - ray_origin

    # Python API changed in 2.91: https://wiki.blender.org/wiki/Reference/Release_Notes/2.91/Python_API
    view_layer_or_depsgraph = bpy.context.view_layer if bpy.app.version[:2] < (2, 91) else bpy.context.view_layer.depsgraph

    has_hit, snapped_location, snapped_normal, face_index, object, matrix = bpy.context.scene.ray_cast(
        view_layer_or_depsgraph, ray_origin, vec)

    randoffset = math.pi
    if has_hit:
        snapped_rotation = snapped_normal.to_track_quat('Z', 'Y').to_euler()
        up = Vector((0, 0, 1))
        props = bpy.context.scene.luxcoreOL.model
        if props.randomize_rotation and snapped_normal.angle(up) < math.radians(10.0):
            randoffset = props.offset_rotation_amount + math.pi + (
                    random.random() - 0.5) * props.randomize_rotation_amount
        else:
            randoffset = props.offset_rotation_amount  # we don't rotate this way on walls and ceilings. + math.pi
        # snapped_rotation.z += math.pi + (random.random() - 0.5) * .2
    else:
        snapped_rotation = mathutils.Quaternion((0, 0, 0, 0)).to_euler()

    snapped_rotation.rotate_axis('Z', randoffset)

    return has_hit, snapped_location, snapped_normal, snapped_rotation, face_index, object, matrix


def floor_raycast(context, mx, my):
    r = context.region
    rv3d = context.region_data
    coord = mx, my

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(r, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(r, rv3d, coord)
    ray_target = ray_origin + (view_vector * 1000)

    # various intersection plane normals are needed for corner cases that might actually happen quite often - in front and side view.
    # default plane normal is scene floor.
    plane_normal = (0, 0, 1)
    if math.isclose(view_vector.x, 0, abs_tol=1e-4) and math.isclose(view_vector.z, 0, abs_tol=1e-4):
        plane_normal = (0, 1, 0)
    elif math.isclose(view_vector.z, 0, abs_tol=1e-4):
        plane_normal = (1, 0, 0)

    snapped_location = mathutils.geometry.intersect_line_plane(ray_origin, ray_target, (0, 0, 0), plane_normal,
                                                               False)
    if snapped_location != None:
        has_hit = True
        snapped_normal = Vector((0, 0, 1))
        face_index = None
        object = None
        matrix = None
        snapped_rotation = snapped_normal.to_track_quat('Z', 'Y').to_euler()

        props = bpy.context.scene.luxcoreOL.model
        if props.randomize_rotation:
            randoffset = props.offset_rotation_amount + math.pi + (
                    random.random() - 0.5) * props.randomize_rotation_amount
        else:
            randoffset = props.offset_rotation_amount + math.pi

        snapped_rotation.rotate_axis('Z', randoffset)

    return has_hit, snapped_location, snapped_normal, snapped_rotation, face_index, object, matrix