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
from bpy.props import BoolProperty, IntProperty, StringProperty, CollectionProperty, PointerProperty

from os import listdir
from os.path import basename, dirname, isfile, join, splitext, exists
from ...utils.lol import utils as lol_utils
from ...utils import get_addon_preferences

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

    user_preferences = get_addon_preferences(context)

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

    asset_index: IntProperty(name="asset_index", default=-1, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        return "Add an asset to local library"


    def execute(self, context):
        scene = context.scene
        ui_props = scene.luxcoreOL.ui
        upload_props = scene.luxcoreOL.upload

        user_preferences = get_addon_preferences(context)

        if len(context.selected_objects) == 0:
            return {'CANCELLED'}

        assets = []
        new_asset = {}
        data_block = set()

        filepath = join(user_preferences.global_dir, 'local_assets_' + ui_props.asset_type.lower() + '.json')
        if isfile(filepath):
            with open(filepath) as file_handle:
                assets = json.loads(file_handle.read())

        if self.asset_index == -1:
            new_asset['name'] = upload_props.name
            new_asset['category'] = upload_props.category

            if ui_props.asset_type == 'MODEL':
                (bbox_min, bbox_max) = calc_bbox(context, context.selected_objects)
                new_asset['bbox_min'] = bbox_min
                new_asset['bbox_max'] = bbox_max
                data_block = set(context.selected_objects)

            elif ui_props.asset_type == 'MATERIAL':
                new_asset['name'] = context.active_object.active_material.name
                new_asset['category'] = upload_props.category
                data_block = {context.active_object.active_material}

            new_asset['url'] = join("local", new_asset['name'].replace(" ", "_")+'.zip')

            assetpath = join(user_preferences.global_dir, ui_props.asset_type.lower(), 'local')
            blendfilepath = join(assetpath, new_asset['name'].replace(' ', '_') + '.blend')
            bpy.data.libraries.write(blendfilepath, data_block, fake_user=True)
            new_asset['hash'] = calc_hash(blendfilepath)
        else:
            new_asset['name'] = upload_props.add_list[self.asset_index]['name']
            new_asset['category'] = upload_props.add_list[self.asset_index]['category']

            if ui_props.asset_type == 'MODEL':
                bbox_min = upload_props.add_list[self.asset_index]['bbox_min']
                bbox_max = upload_props.add_list[self.asset_index]['bbox_max']
                new_asset['bbox_min'] = [bbox_min[0], bbox_min[1], bbox_min[2]]
                new_asset['bbox_max'] = [bbox_max[0], bbox_max[1], bbox_max[2]]

            new_asset['hash'] = upload_props.add_list[self.asset_index]['hash']
            new_asset['url'] = upload_props.add_list[self.asset_index]['url']
            upload_props.add_list[self.asset_index]['thumbnail'].use_fake_user = True

            upload_props.add_list.remove(self.asset_index)

        assets.append(new_asset)

        jsonstr = json.dumps(assets, indent=2)
        with open(filepath, "w") as file_handle:
            file_handle.write(jsonstr)

        if self.asset_index == -1:
            from shutil import copyfile

            if upload_props.autorender:
                # Render thumnnail image in background
                from subprocess import Popen

                studio = '"' + join(dirname(dirname(dirname(__file__))), 'scripts', 'LOL', 'studio.blend') + '"'
                if ui_props.asset_type == 'MATERIAL':
                    studio = '"' + join(dirname(dirname(dirname(__file__))), 'scripts', 'LOL', 'material_thumbnail.blend') + '"'

                script = '"' + join(dirname(dirname(dirname(__file__))), 'scripts', 'LOL', 'render_thumbnail.py') + '"'
                process = Popen(bpy.app.binary_path + ' ' + studio
                                + ' -b --python ' + script + ' -- ' + blendfilepath + ' ' + str(upload_props.samples)
                                + ' ' + ui_props.asset_type.lower())
                process.wait()
                assetpath = join(user_preferences.global_dir, ui_props.asset_type.lower())
                thumbnailname = new_asset['name'].replace(' ', '_') + '.jpg'
                join(assetpath, 'preview', 'local', thumbnailname)

                copyfile(join(assetpath, 'preview', 'full', 'local', thumbnailname),
                         join(assetpath, 'preview', 'local', thumbnailname))
            else:
                if upload_props.thumbnail.filepath !=  join(user_preferences.global_dir, ui_props.asset_type.lower(), 'preview', 'full', 'local', new_asset['name'].replace(" ", "_") + ".jpg"):
                    copyfile(upload_props.thumbnail.filepath, join(user_preferences.global_dir, ui_props.asset_type.lower(), 'preview', 'full', 'local', new_asset['name'].replace(" ", "_") + ".jpg"))
                copyfile(upload_props.thumbnail.filepath, join(user_preferences.global_dir, ui_props.asset_type.lower(), 'preview', 'local', new_asset['name'].replace(" ", "_") + ".jpg"))

            assetpath = join(user_preferences.global_dir, ui_props.asset_type.lower())
            img = bpy.data.images.load(join(assetpath, 'preview', 'local', new_asset['name'].replace(" ", "_") + ".jpg"))
            img.scale(128, 128)
            img.save()
            bpy.data.images.remove(img)

        lol_utils.download_table_of_contents(context)
        lol_utils.load_previews(context, ui_props.asset_type)

        return {'FINISHED'}


class LOLScanLocalOperator(Operator):
    bl_idname = 'scene.luxcore_ol_scan_local'
    bl_label = 'LuxCore Online Library Scan Local Assets'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def description(cls, context, properties):
        return "Find local assets and add them to local library"


    def execute(self, context):
        scene = context.scene
        ui_props = scene.luxcoreOL.ui
        upload_props = scene.luxcoreOL.upload

        user_preferences = get_addon_preferences(context)
        assetpath = join(user_preferences.global_dir, ui_props.asset_type.lower(), 'local')

        files = [f for f in listdir(assetpath) if isfile(join(assetpath, f))]

        if len(upload_props.add_list) > 0:
            upload_props.add_list.clear()

        assets = lol_utils.load_local_TOC(context, ui_props.asset_type.lower())

        hashlist = [asset["hash"] for asset in assets]

        for f in files:
            hash = calc_hash(join(assetpath, f))
            if not hash in hashlist:
                new_asset = upload_props.add_list.add()
                new_asset["name"] = splitext(f)[0].replace("_", " ")
                new_asset["category"] = "Misc"
                new_asset["hash"] = hash

                tpath = join(user_preferences.global_dir, ui_props.asset_type.lower(), "preview", "local",
                                     splitext(f)[0] + '.jpg')

                if exists(tpath):
                    img = bpy.data.images.load(tpath)
                    img.name = '.LOL_preview'
                else:
                    rootdir = dirname(dirname(dirname(__file__)))
                    path = join(rootdir, 'thumbnails', 'thumbnail_notready.jpg')
                    img = bpy.data.images.load(path)
                    img.name = '.LOL_preview'

                new_asset["thumbnail"] = img

                with bpy.data.libraries.load(join(assetpath, f), link=True) as (data_from, data_to):
                    data_to.objects = [name for name in data_from.objects]

                bbox_min, bbox_max = calc_bbox(context, data_to.objects)

                for obj in data_to.objects:
                    bpy.data.objects.remove(obj)

                new_asset['bbox_min'] = bbox_min
                new_asset['bbox_max'] = bbox_max
                new_asset["url"] = join("local", splitext(f)[0]+".zip")
        return {'FINISHED'}