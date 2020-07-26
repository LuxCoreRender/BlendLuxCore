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
import json
import hashlib

from bpy.types import Operator
from bpy.props import BoolProperty, IntProperty, StringProperty, CollectionProperty

from os.path import basename, dirname, isfile, join
from ...utils.lol import utils as lol_utils

from mathutils import Vector

def calc_bbox(context, objects):
    bbox_min = [10000, 10000, 10000]
    bbox_max = [-10000, -10000, -10000]

    deps = bpy.context.evaluated_depsgraph_get()

    for obj in objects:
        obj = obj.evaluated_get(deps)

        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

        for corner in bbox_corners:
            bbox_min[0] = min(bbox_min[0], corner[0])
            bbox_min[1] = min(bbox_min[1], corner[1])
            bbox_min[2] = min(bbox_min[2], corner[2])

            bbox_max[0] = max(bbox_max[0], corner[0])
            bbox_max[1] = max(bbox_max[1], corner[1])
            bbox_max[2] = max(bbox_max[2], corner[2])

    return (bbox_min, bbox_max)


def calc_hash(filename):
    BLOCK_SIZE = 65536
    file_hash = hashlib.sha256()
    with open(filename, 'rb') as file:
        block = file.read(BLOCK_SIZE)
        while len(block) > 0:
            file_hash.update(block)
            block = file.read(BLOCK_SIZE)
    return file_hash.hexdigest()


def scale_scene(context):
    depsgraph = context.evaluated_depsgraph_get()


def render_thumbnail(args):
    from ...utils.compatibility import run
    (context, assetfile, asset_type) = args

    name = basename(dirname(dirname(dirname(__file__))))
    user_preferences = context.preferences.addons[name].preferences


    if asset_type == 'MODEL':
        luxball = 'material_thumbnail.blend'
        with bpy.data.libraries.load(luxball, link=True) as (data_from, data_to):
            data_to.scene = data_from.scene

    elif asset_type == 'MATERIAL':
        mat = context.active_object.active_material

        luxball = 'material_thumbnail.blend'
        with bpy.data.libraries.load(luxball, link=True) as (data_from, data_to):
            data_to.scene = data_from.scene

        bpy.context.view_layer.objects.active = bpy.data.objects['Luxball']

        bpy.data.objects['Luxball'].material_slots[0].material = mat
        bpy.context.view_layer.objects.active = bpy.data.objects['Luxball ring']

        bpy.data.objects['Luxball ring'].material_slots[0].material = mat
        run()
        bpy.context.scene.render.filepath = join(user_preferences.global_dir, 'material','preview', + mat.name + '.jpg')
        if not isfile(bpy.context.scene.render.filepath):
            bpy.ops.render.render(write_still=True)

        mat.user_clear()

        leftOverMatBlocks = [block for block in bpy.data.materials if block.users == 0]
        for block in leftOverMatBlocks:
            bpy.data.materials.remove(block)

        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()


class LOLAddLocalOperator(Operator):
    bl_idname = 'scene.luxcore_ol_add_local'
    bl_label = 'LuxCore Online Library Add Assets Local'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def description(cls, context, properties):
        return "Add an asset to local library"


    def execute(self, context):
        scene = context.scene
        ui_props = scene.luxcoreOL.ui
        upload_props = scene.luxcoreOL.upload

        name = basename(dirname(dirname(dirname(__file__))))
        user_preferences = context.preferences.addons[name].preferences

        if len(context.selected_objects) == 0:
            return {'CANCELLED'}

        assets = []
        new_asset = {}
        data_block = set()

        new_asset['name'] = upload_props.name
        new_asset['category'] = upload_props.category
        new_asset['url'] = upload_props.name.replace(" ", "_")+'.zip'

        if ui_props.asset_type == 'MODEL':
            (bbox_min, bbox_max) = calc_bbox(context, context.selected_objects)
            new_asset['bbox_min'] = bbox_min
            new_asset['bbox_max'] = bbox_max
            data_block = set(context.selected_objects)

        elif ui_props.asset_type == 'MATERIAL':
            data_block = set(context.active_object.active_material)

        filepath = join(user_preferences.global_dir, 'local_assets_' + ui_props.asset_type.lower() + '.json')
        if isfile(filepath):
            with open(filepath) as file_handle:
                assets = json.loads(file_handle.read())

        assetpath = join(user_preferences.global_dir, ui_props.asset_type.lower())
        blendfilepath = join(assetpath, upload_props.name.replace(" ", "_") + ".blend")
        bpy.data.libraries.write(blendfilepath, data_block, fake_user = True)

        new_asset['hash'] = calc_hash(blendfilepath)
        assets.append(new_asset)

        jsonstr = json.dumps(assets, indent=2)
        with open(filepath, "w") as file_handle:
            file_handle.write(jsonstr)

        if upload_props.autorender:
            # Render thumnnail image in background
            from subprocess import Popen

            studio = '"' + join(dirname(dirname(dirname(__file__))), 'scripts', 'LOL', 'studio.blend') + '"'
            script = '"' + join(dirname(dirname(dirname(__file__))), 'scripts', 'LOL', 'render_thumbnail.py') + '"'

            process = Popen(bpy.app.binary_path + ' ' + studio
                            + ' -b --python ' + script + ' -- ' + blendfilepath + ' ' + str(upload_props.samples))
            process.wait()
        else:
            from shutil import copyfile
            copyfile(upload_props.thumbnail.filepath, join(user_preferences.global_dir, ui_props.asset_type.lower(), 'preview', upload_props.name.replace(" ", "_") + ".jpg"))

        lol_utils.download_table_of_contents(context)
        lol_utils.load_previews(context, ui_props.asset_type)

        return {'FINISHED'}
