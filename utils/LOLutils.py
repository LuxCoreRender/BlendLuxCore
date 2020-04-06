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

import bpy
import uuid
from os.path import basename, dirname
import json
import hashlib
import tempfile
import os
import urllib.request
import urllib.error
import zipfile
from mathutils import Vector, Matrix
import threading

LOL_HOST_URL = "https://luxcorerender.org/lol"

download_threads = []

def download_table_of_contents(self, context):
    print("=======================================")
    print("Download table of contents")
    print()
    try:
        request = urllib.request.urlopen(LOL_HOST_URL + "/assets.json", timeout=60)

        assets = json.loads(request.read())

        print("Found %i assets in library." % len(assets))
        context.scene.luxcoreOL['assets'] = assets

    except ConnectionError as error:
        self.report({"ERROR"}, "Connection error: Could not download table of contents")
        return {"CANCELLED"}


def download_thumbnail(self, context, asset, index):
    name = basename(dirname(dirname(__file__)))
    user_preferences = context.preferences.addons[name].preferences

    imagename = asset['url'][:-4] + '.jpg'
    print("=======================================")
    print("Download thumbnail: ", imagename)
    print()

    try:
        thumbnailpath = os.path.join(user_preferences.global_dir, "model", "preview", imagename)

        with urllib.request.urlopen(LOL_HOST_URL + "/assets/preview/" + imagename, timeout=60) as url_handle, \
                open(thumbnailpath, "wb") as file_handle:
            file_handle.write(url_handle.read())

        if os.path.exists(thumbnailpath):
            imagename = previmg_name(index)
            img = bpy.data.images.get(imagename)
            if img is None:
                img = bpy.data.images.load(thumbnailpath)
                img.colorspace_settings.name = 'Linear'
                img.name = imagename

        if img == None:
            img = get_thumbnail('thumbnail_notready.jpg')

        return img

    except ConnectionError as error:
        self.report({"ERROR"}, "Connection error: Could not download "+ imagename)
        return {"CANCELLED"}


def calc_hash(filename):
    BLOCK_SIZE = 65536
    file_hash = hashlib.sha256()
    with open(filename, 'rb') as file:
        block = file.read(BLOCK_SIZE)
        while len(block) > 0:
            file_hash.update(block)
            block = file.read(BLOCK_SIZE)
    return file_hash.hexdigest()


def download_file(context, asset):
    name = basename(dirname(dirname(__file__)))
    user_preferences = context.preferences.addons[name].preferences

    #print(asset["name"])
    filename = asset["name"].replace(" ", "_")
    filepath = os.path.join(user_preferences.global_dir, "model", filename + '.blend')

    download = False
    if not os.path.exists(filepath):
        download = True
    else:
        hash = calc_hash(filepath)
        if hash != asset["hash"]:
            download = True

    if download:
        with tempfile.TemporaryDirectory() as temp_dir_path:
            temp_zip_path = os.path.join(temp_dir_path, filename)

            url = LOL_HOST_URL + "/assets/" + asset["url"]
            try:
                print("Downloading:", url)
                with urllib.request.urlopen(url, timeout=60) as url_handle, \
                        open(temp_zip_path, "wb") as file_handle:
                    file_handle.write(url_handle.read())

                    with zipfile.ZipFile(temp_zip_path) as zf:
                        print("Extracting zip to", os.path.join(user_preferences.global_dir, "model"))
                        zf.extractall(os.path.join(user_preferences.global_dir, "model"))

            except urllib.error.URLError as err:
                print("Could not download: %s" % err)
                return False

            print("Download finished")

    hash = calc_hash(filepath)
    if hash != asset["hash"]:
        print("File has wrong hash number: %s" % hash)
        return False

    return True


#TODO: Implement threaded downloader
class Downloader(threading.Thread):
    def __init__(self, asset_data, tcom, scene_id, api_key):
        super(Downloader, self).__init__()
        self.asset_data = asset_data
        self.tcom = tcom
        self.scene_id = scene_id
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        print("Download Thread running")
        return self._stop_event.is_set()

    # def main_download_thread(asset_data, tcom, scene_id, api_key):
    def run(self):
        print("Download Thread running")
        # '''try to download file from blenderkit'''
        # asset_data = self.asset_data
        # tcom = self.tcom
        # scene_id = self.scene_id
        #
        # # TODO get real link here...
        # has_url = get_download_url(asset_data, scene_id, api_key, tcom=tcom)
        #
        # if not has_url:
        #     tasks_queue.add_task(
        #         (ui.add_report, ('Failed to obtain download URL for %s.' % asset_data['name'], 5, colors.RED)))
        #     return
        # if tcom.error:
        #     return
        # # only now we can check if the file already exists. This should have 2 levels, for materials and for brushes
        # # different than for the non free content. delete is here when called after failed append tries.
        # if check_existing(asset_data) and not tcom.passargs.get('delete'):
        #     # this sends the thread for processing, where another check should occur, since the file might be corrupted.
        #     tcom.downloaded = 100
        #     utils.p('not downloading, trying to append again')
        #     return
        #
        # file_name = paths.get_download_filenames(asset_data)[0]  # prefer global dir if possible.
        # # for k in asset_data:
        # #    print(asset_data[k])
        # if self.stopped():
        #     utils.p('stopping download: ' + asset_data['name'])
        #     return
        #
        # with open(file_name, "wb") as f:
        #     print("Downloading %s" % file_name)
        #     headers = utils.get_headers(api_key)
        #
        #     response = requests.get(asset_data['url'], stream=True)
        #     total_length = response.headers.get('Content-Length')
        #
        #     if total_length is None:  # no content length header
        #         f.write(response.content)
        #     else:
        #         tcom.file_size = int(total_length)
        #         dl = 0
        #         for data in response.iter_content(chunk_size=4096):
        #             dl += len(data)
        #             tcom.downloaded = dl
        #             tcom.progress = int(100 * tcom.downloaded / tcom.file_size)
        #             f.write(data)
        #             if self.stopped():
        #                 utils.p('stopping download: ' + asset_data['name'])
        #                 f.close()
        #                 os.remove(file_name)
        #                 return


class ThreadCom:  # object passed to threads to read background process stdout info
    def __init__(self):
        self.file_size = 1000000000000000  # property that gets written to.
        self.downloaded = 0
        self.lasttext = ''
        self.error = False
        self.report = ''
        self.progress = 0.0
        self.passargs = {}


def link_asset(self, context, asset, location, rotation):
    print("Link asset")
    name = basename(dirname(dirname(__file__)))
    user_preferences = context.preferences.addons[name].preferences

    filename = asset["url"]
    filepath = os.path.join(user_preferences.global_dir, "model", filename[:-3]+'blend')

    download = False
    if not os.path.exists(filepath):
        download = True
    else:
        hash = calc_hash(filepath)
        if hash != asset["hash"]:
            print("hash number doesn't match: %s" % hash)
            download = True

    if download:
        if not download_file(context, asset):
            return False

    with bpy.data.libraries.load(filepath, link=True) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name not in ["Plane", "Camera"]]


    bpy.ops.object.empty_add(type='PLAIN_AXES', location=Vector(location), rotation=rotation)
    main_object = bpy.context.view_layer.objects.active
    main_object.name = asset["name"]
    bbox_min = asset["bbox_min"]
    bbox_max = asset["bbox_max"]

    main_object.empty_display_size = 0.5*max(bbox_max[0] - bbox_min[0], bbox_max[1] - bbox_min[1], bbox_max[2] - bbox_min[2])
    main_object.instance_type = 'COLLECTION'
    main_object.matrix_world.translation = location

    bbox_center = 0.5 * Vector((bbox_max[0] + bbox_min[0], bbox_max[1] + bbox_min[1], 0.0))

    col = bpy.data.collections.new(asset["name"])
    col.instance_offset = bbox_center
    main_object.instance_collection = col

    # Objects have to be linked to show up in a scene
    for obj in data_to.objects:
        col.objects.link(obj)

    return True


def get_search_props():
    scene = bpy.context.scene
    if scene is None:
        return
    uiprops = scene.luxcoreOL.ui
    props = None
    if uiprops.asset_type == 'MODEL':
        if not hasattr(scene, 'LuxCoreAssets_models'):
            return
        props = scene.LuxCoreAssets_models
    if uiprops.asset_type == 'SCENE':
        if not hasattr(scene, 'LuxCoreAssets_scene'):
            return
        props = scene.LuxCoreAssets_scene
    if uiprops.asset_type == 'MATERIAL':
        if not hasattr(scene, 'LuxCoreAssets_mat'):
            return
        props = scene.LuxCoreAssets_mat

    if uiprops.asset_type == 'TEXTURE':
        if not hasattr(scene, 'LuxCoreAssets_tex'):
            return
        # props = scene.LuxCoreAssets_tex

    if uiprops.asset_type == 'BRUSH':
        if not hasattr(scene, 'LuxCoreAssets_brush'):
            return;
        props = scene.LuxCoreAssets_brush
    return props


def save_prefs(self, context):
    # first check context, so we don't do this on registration or blender startup
    if not bpy.app.background: #(hasattr kills blender)
        # TODO:
        #user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        test = 1
        #prefs = {
        #    'global_dir': user_preferences.global_dir,
        #}
        #try:
        #    fpath = paths.BLENDERKIT_SETTINGS_FILENAME
        #    if not os.path.exists(paths._presets):
        #        os.makedirs(paths._presets)
        #    f = open(fpath, 'w')
        #    with open(fpath, 'w') as s:
        #        json.dump(prefs, s)
        #except Exception as e:
        #    print(e)


def default_global_dict():
    from os.path import expanduser
    home = expanduser("~")
    return home + os.sep + 'LuxCoreOnlineLibrary_data'


def get_scene_id():
    '''gets scene id and possibly also generates a new one'''
    bpy.context.scene['uuid'] = bpy.context.scene.get('uuid', str(uuid.uuid4()))
    return bpy.context.scene['uuid']


def guard_from_crash():
    '''Blender tends to crash when trying to run some functions with the addon going through unregistration process.'''
    #if bpy.context.preferences.addons.get('BlendLuxCore') is None:
    #    return False
    #if bpy.context.preferences.addons['BlendLuxCore'].preferences is None:
    #    return False
    return True


def get_thumbnail(imagename):
    name = dirname(dirname(__file__))
    path = os.path.join(name, 'thumbnails', imagename)

    imagename = '.%s' % imagename
    img = bpy.data.images.get(imagename)

    if img == None:
        img = bpy.data.images.load(path)
        img.colorspace_settings.name = 'Linear'
        img.name = imagename
        img.name = imagename

    return img


def previmg_name(index, fullsize=False):
    if not fullsize:
        return '.LOL_preview_'+ str(index).zfill(2)
    else:
        return '.LOL_preview_full_' + str(index).zfill(2)


def load_previews(context, assets):
    name = basename(dirname(dirname(__file__)))
    user_preferences = context.preferences.addons[name].preferences

    if assets is not None and len(assets) != 0:
        i = 0
        for asset in assets:
            tpath = os.path.join(user_preferences.global_dir, "model", "preview", asset['url'][:-4] + '.jpg')
            imgname = previmg_name(i)

            if os.path.exists(tpath):
                img = bpy.data.images.get(imgname)
                if img is None:
                    img = bpy.data.images.load(tpath)
                    img.name = imgname
                elif img.filepath != tpath:
                    # had to add this check for autopacking files...
                    if img.packed_file is not None:
                        img.unpack(method='USE_ORIGINAL')
                    img.filepath = tpath
                    img.reload()
                img.colorspace_settings.name = 'Linear'
            i += 1