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
#
#  This code is based on the Blenderkit Addon
#  Homepage: https://www.blenderkit.com/
#  Sourcecode: https://github.com/blender/blender-addons/tree/master/blenderkit
#
# #####

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
from ..handlers.LOLtimer import timer_update

LOL_HOST_URL = "https://luxcorerender.org/lol"

download_threads = []

def download_table_of_contents(self, context):
    # print("=======================================")
    # print("Download table of contents")
    # print()
    try:
        request = urllib.request.urlopen(LOL_HOST_URL + "/assets.json", timeout=60)

        assets = json.loads(request.read())

        # print("Found %i assets in library." % len(assets))
        context.scene.luxcoreOL['assets'] = assets
        request.close()
    except ConnectionError as error:
        self.report({"ERROR"}, "Connection error: Could not download table of contents")
        return {"CANCELLED"}


def get_categories(context):
    uiprops = context.scene.luxcoreOL
    assets = context.scene.luxcoreOL['assets']
    categories = {}

    for asset in assets:
        cat = asset['category']
        if not cat in categories:
            categories[cat] = 1
        else:
            categories[cat] = categories[cat] + 1

    context.scene.luxcoreOL['categories'] = categories


def download_thumbnail(self, context, asset, index):
    name = basename(dirname(dirname(__file__)))
    user_preferences = context.preferences.addons[name].preferences

    imagename = asset['url'][:-4] + '.jpg'
    # print("=======================================")
    # print("Download thumbnail: ", imagename)
    # print()

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


def is_downloading(asset):
    global download_threads
    for thread_data in download_threads:
        if asset['hash'] == thread_data[1]['hash']:
            # print(asset["name"], "is downloading")
            return thread_data[2]

    return None


def download_file(asset, location, rotation):
    downloader = {'location': (location[0],location[1],location[2]), 'rotation': (rotation[0],rotation[1],rotation[2])}
    tcom  = is_downloading(asset)
    if tcom is None:
        tcom = ThreadCom()
        tcom.passargs['downloaders'] = [downloader]

        downloadthread = Downloader(asset, tcom)
        downloadthread.start()

        download_threads.append([downloadthread, asset, tcom])
        bpy.app.timers.register(timer_update)
    else:
        tcom.passargs['downloaders'].append(downloader)

    return True


class Downloader(threading.Thread):
    def __init__(self, asset, tcom):
        super(Downloader, self).__init__()
        self.asset = asset
        self.tcom = tcom
        self._stop_event = threading.Event()

    def stop(self):
        print("Download Thread stopped")
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    # def main_download_thread(asset_data, tcom, scene_id, api_key):
    def run(self):
        name = basename(dirname(dirname(__file__)))
        user_preferences = bpy.context.preferences.addons[name].preferences

        print("Download Thread running")
        filename = self.asset["url"]
        tcom = self.tcom

        with tempfile.TemporaryDirectory() as temp_dir_path:
            temp_zip_path = os.path.join(temp_dir_path, filename)
            # print(temp_zip_path)
            url = LOL_HOST_URL + "/assets/" + filename
            try:
                print("Downloading:", url)

                with urllib.request.urlopen(url, timeout=60) as url_handle, \
                        open(temp_zip_path, "wb") as file_handle:
                    total_length = url_handle.headers.get('Content-Length')
                    tcom.file_size = int(total_length)

                    dl = 0
                    data = url_handle.read(8192)
                    file_handle.write(data)
                    while len(data) == 8192:
                        data = url_handle.read(8192)
                        dl += len(data)
                        tcom.downloaded = dl
                        tcom.progress = int(100 * tcom.downloaded / tcom.file_size)

                        file_handle.write(data)
                        if self.stopped():
                            url_handle.close()
                            return
                print("Download finished")
                with zipfile.ZipFile(temp_zip_path) as zf:
                    print("Extracting zip to", os.path.join(user_preferences.global_dir, "model"))
                    zf.extractall(os.path.join(user_preferences.global_dir, "model"))
                tcom.finished = True

            except urllib.error.URLError as err:
                print("Could not download: %s" % err)


class ThreadCom:  # object passed to threads to read background process stdout info
    def __init__(self):
        self.file_size = 1000000000000000  # property that gets written to.
        self.downloaded = 0
        self.progress = 0.0
        self.finished = False
        self.passargs = {}


def link_asset(context, asset, location, rotation):
    name = basename(dirname(dirname(__file__)))
    user_preferences = context.preferences.addons[name].preferences

    filename = asset["url"]
    filepath = os.path.join(user_preferences.global_dir, "model", filename[:-3] + 'blend')

    scene = context.scene
    link_model = (scene.luxcoreOL.model.append_method == 'LINK_COLLECTION')

    with bpy.data.libraries.load(filepath, link=link_model) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name not in ["Plane", "Camera"]]

    bbox_min = asset["bbox_min"]
    bbox_max = asset["bbox_max"]
    bbox_center = 0.5 * Vector((bbox_max[0] + bbox_min[0], bbox_max[1] + bbox_min[1], 0.0))

    # TODO: Check if asset is already used in scene and override append/link selection
    # If the same model is first linked and then appended it breaks relationships and transformaton in blender

    # Add new collection, where the assets are placed into
    col = bpy.data.collections.new(asset["name"])

    # Add parent empty for asset collection
    main_object = bpy.data.objects.new(asset["name"], None)
    main_object.empty_display_size = 0.5 * max(bbox_max[0] - bbox_min[0], bbox_max[1] - bbox_min[1],
                                               bbox_max[2] - bbox_min[2])

    main_object.location = location
    main_object.rotation_euler = rotation
    main_object.empty_display_size = 0.5*max(bbox_max[0] - bbox_min[0], bbox_max[1] - bbox_min[1], bbox_max[2] - bbox_min[2])

    if link_model:
        main_object.instance_type = 'COLLECTION'
        main_object.instance_collection = col
        col.instance_offset = bbox_center
    else:
        scene.collection.children.link(col)

    scene.collection.objects.link(main_object)

    # Objects have to be linked to show up in a scene
    for obj in data_to.objects:
        if not link_model:
            obj.data.make_local()
            parent = obj
            while parent.parent != None:
                parent = parent.parent

            if parent != main_object:
                parent.parent = main_object
                parent.matrix_parent_inverse = main_object.matrix_world.inverted() @ Matrix.Translation(-1*bbox_center)

        # Add objects to asset collection
        col.objects.link(obj)


def load_asset(context, asset, location, rotation):
    name = basename(dirname(dirname(__file__)))
    user_preferences = context.preferences.addons[name].preferences

    filename = asset["url"]
    filepath = os.path.join(user_preferences.global_dir, "model", filename[:-3]+'blend')

    ''' Check if model is cached '''
    download = False
    if not os.path.exists(filepath):
        download = True
    else:
        hash = calc_hash(filepath)
        if hash != asset["hash"]:
            print("hash number doesn't match: %s" % hash)
            download = True

    if download:
        print("Download asset")
        download_file(asset, location, rotation)
    else:
        link_asset(context, asset, location, rotation)


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