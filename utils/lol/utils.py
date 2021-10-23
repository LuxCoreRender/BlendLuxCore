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
from os.path import basename, dirname, join, isfile, splitext
import hashlib
import tempfile
import os
import urllib.error
from mathutils import Vector, Matrix
import threading
from threading import _MainThread, Thread, Lock
from ...handlers.lol.timer import timer_update
from ...utils import get_addon_preferences, compatibility

LOL_HOST_URL = "https://luxcorerender.org/lol"
LOL_VERSION = "v2.5"

download_threads = []
bg_threads = []
stop_check_cache = False

def load_local_TOC(context, asset_type):
    import json

    assets = []

    name = basename(dirname(dirname(dirname(__file__))))
    user_preferences = context.preferences.addons[name].preferences

    filepath = join(user_preferences.global_dir, 'local_assets_' + asset_type + '.json')
    if isfile(filepath):
        with open(filepath) as file_handle:
            assets = json.loads(file_handle.read())

    for asset in assets:
        asset['downloaded'] = 100.0
        asset['local'] = True
        asset['patreon'] = False
        asset['locked'] = False

    return assets


def load_patreon_assets(context):
    name = basename(dirname(dirname(dirname(__file__))))
    user_preferences = context.preferences.addons[name].preferences

    #check if local file is available
    filepath = join(user_preferences.global_dir, 'assets_model_blendermarket.json')
    if os.path.exists(filepath):
        with open(filepath) as file_handle:
            import json
            assets = json.load(file_handle)
            for asset in assets:
                asset['downloaded'] = 0.0
                asset['local'] = False
                asset['patreon'] = True
                asset['locked'] = True
                filename = asset["url"]
                filepath = join(user_preferences.global_dir, "model", splitext(filename)[0] + '.blend')

                if os.path.exists(filepath):
                    asset['locked'] = False
    else:
        urlstr = LOL_HOST_URL + "/" + LOL_VERSION + "/assets_model_blendermarket.json"
        with urllib.request.urlopen(urlstr, timeout=60) as request:
            import json
            assets = json.load(request)

            #cache file for future offline work
            with open(filepath, 'w') as file:
                file.write(json.dumps(assets, indent=2))

            for asset in assets:
                asset['downloaded'] = 0.0
                asset['local'] = False
                asset['patreon'] = True
                asset['locked'] = True
                filename = asset["url"]
                filepath = join(user_preferences.global_dir, 'model', splitext(filename)[0] + '.blend')

                if os.path.exists(filepath):
                    asset['locked'] = False

    return assets


def download_table_of_contents(context):
    scene = context.scene
    ui_props = context.scene.luxcoreOL.ui
    name = basename(dirname(dirname(dirname(__file__))))
    user_preferences = context.preferences.addons[name].preferences

    try:
        for threaddata in bg_threads:
            tag, bg_task = threaddata
            if tag == "check_cache":
                global stop_check_cache
                stop_check_cache = True

        # check if local file is available
        filepath = join(user_preferences.global_dir, 'assets_model.json')
        if os.path.exists(filepath):
            with open(filepath) as file_handle:
                import json
                assets = json.load(file_handle)

                for asset in assets:
                    asset['downloaded'] = 0.0
                    asset['local'] = False
                    asset['patreon'] = False
                    asset['locked'] = False

        else:
            import urllib.request
            urlstr = LOL_HOST_URL + "/" + LOL_VERSION + "/assets_model.json"
            with urllib.request.urlopen(urlstr, timeout=60) as request:
                import json
                assets = json.load(request)
                # cache file for future offline work
                with open(filepath, 'w') as file:
                    file.write(json.dumps(assets, indent=2))

                for asset in assets:
                    asset['downloaded'] = 0.0
                    asset['local'] = False
                    asset['patreon'] = False
                    asset['locked'] = False


        assets.extend(load_local_TOC(context, 'model'))
        assets.extend(load_patreon_assets(context))
        scene.luxcoreOL.model['assets'] = assets

        # with urllib.request.urlopen(LOL_HOST_URL + "/assets_scene.json", timeout=60) as request:
        #     import json
        #     assets = json.loads(request.read())
        #     for asset in scene.luxcoreOL.scene['assets']:
        #         asset['downloaded'] = 0.0
        #         asset['local'] = False
        #
        #     assets.extend(load_local_TOC(context, 'scene'))
        #     scene.luxcoreOL.scene['assets'] = assets

        # check if local file is available
        filepath = join(user_preferences.global_dir, 'assets_material.json')
        if os.path.exists(filepath):
            with open(filepath) as file_handle:
                import json
                assets = json.load(file_handle)
                for asset in assets:
                    asset['downloaded'] = 0.0
                    asset['local'] = False
                    asset['patreon'] = False
                    asset['locked'] = False
        else:
            import urllib.request
            urlstr = LOL_HOST_URL + "/" + LOL_VERSION + "/assets_material.json"
            with urllib.request.urlopen(urlstr, timeout=60) as request:
                import json
                assets = json.load(request)
                # cache file for future offline work
                with open(filepath, 'w') as file:
                    file.write(json.dumps(assets, indent=2))

                for asset in assets:
                    asset['downloaded'] = 0.0
                    asset['local'] = False
                    asset['patreon'] = False
                    asset['locked'] = False

        assets.extend(load_local_TOC(context, 'material'))
        scene.luxcoreOL.material['assets'] = assets

        ui_props.ToC_loaded = True
        init_categories(context)
        bg_task = Thread(target=check_cache, args=(context, ))
        bg_threads.append(["check_cache", bg_task])
        bg_task.start()
        return True
    except ConnectionError as error:
        print("Connection error: Could not download table of contents")
        print(error)
        return False
    except urllib.error.URLError as error:
        print("URL error: Could not download table of contents")
        print(error)

        return False

    finally:
        try:
            request.close()
        except NameError:
            pass

def init_categories(context):
    scene = context.scene
    ui_props = scene.luxcoreOL.ui
    categories = {}

    assets = get_search_props(context)

    if assets == None or len(assets) == 0:
        return

    if ui_props.local:
        assets = [asset for asset in assets if asset['local']]

    if ui_props.free_only:
        assets = [asset for asset in assets if not asset['locked']]

    for asset in assets:
        cat = asset['category']
        try:
            categories[cat] += 1
        except KeyError:
            categories[cat] = 1

    if ui_props.asset_type == 'MODEL':
        asset_props = scene.luxcoreOL.model
    if ui_props.asset_type == 'SCENE':
        asset_props = scene.luxcoreOL.scene
    if ui_props.asset_type == 'MATERIAL':
        asset_props = scene.luxcoreOL.material

    asset_props['categories'] = categories


def check_cache(args):
    (context) = args
    name = basename(dirname(dirname(dirname(__file__))))
    user_preferences = context.preferences.addons[name].preferences
    global stop_check_cache

    user_preferences = get_addon_preferences(context)
    scene = context.scene
    assets = scene.luxcoreOL.model['assets']
    for asset in assets:
        if stop_check_cache:
            break
        filename = asset["url"]
        filepath = join(user_preferences.global_dir, "model", splitext(filename)[0] + '.blend')

        if os.path.exists(filepath):
            if calc_hash(filepath) == asset["hash"]:
                asset['downloaded'] = 100.0

    # assets = scene.luxcoreOL.scene['assets']
    # for asset in assets:
    #     filename = asset["url"]
    #     filepath = join(user_preferences.global_dir, "scene", splitext(filename)[0] + '.blend')
    #
    #     if os.path.exists(filepath):
    #         if calc_hash(filepath) == asset["hash"]:
    #             asset['downloaded'] = 100.0

    assets = scene.luxcoreOL.material['assets']
    for asset in assets:
        if stop_check_cache:
            break
        filename = asset["url"]
        filepath = join(user_preferences.global_dir, "material", splitext(filename)[0] + '.blend')

        if os.path.exists(filepath):
            if calc_hash(filepath) == asset["hash"]:
                asset['downloaded'] = 100.0

    stop_check_cache = False

    for threaddata in bg_threads:
        tag, bg_task = threaddata
        if tag == "check_cache":
            bg_threads.remove(threaddata)


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
        if thread_data[2].passargs['thumbnail']:
            continue
        if asset['hash'] == thread_data[1]['hash']:
            return thread_data[2]
    return None


def download_file(asset_type, asset, location, rotation, target_object, target_slot):
    downloader = {'location': (location[0],location[1],location[2]), 'rotation': (rotation[0],rotation[1],rotation[2]),
                  'target_object': target_object, 'target_slot': target_slot}
    if asset['local']:
        return True

    tcom = is_downloading(asset)
    if tcom is None:
        tcom = ThreadCom()
        tcom.passargs['downloaders'] = [downloader]
        tcom.passargs['thumbnail'] = False
        tcom.passargs['asset type'] = asset_type
        asset_data = asset.to_dict()

        downloadthread = Downloader(asset_data, tcom)

        download_threads.append([downloadthread, asset_data, tcom])
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
        # print("Download Thread stopped")
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    # def main_download_thread(asset_data, tcom, scene_id, api_key):
    def run(self):
        import urllib.request
        user_preferences = get_addon_preferences(bpy.context)

        # print("Download Thread running")
        tcom = self.tcom

        if tcom.passargs['thumbnail']:
            # Thumbnail  download
            if tcom.passargs['asset type'] == 'MATERIAL':
                imagename = self.asset['name'].replace(" ", "_") + '.jpg'
            else:
                imagename = splitext(self.asset['url'])[0] + '.jpg'

            thumbnailpath = os.path.join(user_preferences.global_dir, tcom.passargs['asset type'].lower(), 'preview',
                                         'full', imagename)
            url = LOL_HOST_URL + "/" + tcom.passargs['asset type'].lower() + "/preview/" + imagename
            try:
                with urllib.request.urlopen(url, timeout=60) as url_handle, open(thumbnailpath, "wb") as file_handle:
                    file_handle.write(url_handle.read())

                thumbnailpath_low = os.path.join(user_preferences.global_dir, tcom.passargs['asset type'].lower(),
                                             'preview', imagename)

                from shutil import copyfile
                copyfile(thumbnailpath, thumbnailpath_low)

                img = bpy.data.images.load(thumbnailpath_low)
                img.scale(128, 128)
                img.save()
                bpy.data.images.remove(img)

                self.asset['thumbnail'] = bpy.data.images.load(thumbnailpath_low)
                self.asset['thumbnail'].name = '.LOL_preview'

                img = self.asset['thumbnail']
                if bpy.app.version < (2, 83, 0):
                    # Needed in old Blender versions so the images are not too dark
                    img.colorspace_settings.name = 'Linear'

            except ConnectionError as error:
                print("Connection error: Could not download " + imagename)
                print(error)
            except TimeoutError as error:
                print("TimeoutError error: Could not download " + imagename)
                print(error)
            except urllib.error.HTTPError as error:
                print("HTTPError error: Could not download " + imagename)
                print(error)

            finally:
                tcom.finished = True
                try:
                    url_handle.close()
                except NameError:
                    pass
        else:
            #Asset download
            filename = self.asset["url"]

            with tempfile.TemporaryDirectory() as temp_dir_path:
                temp_zip_path = os.path.join(temp_dir_path, filename)
                url = LOL_HOST_URL + "/" + tcom.passargs['asset type'].lower() + "/" + filename
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

                            # Stop download if Blender is closed
                            for thread in threading.enumerate():
                                if isinstance(thread, _MainThread):
                                    if not thread.is_alive():
                                        self.stop()

                            file_handle.write(data)
                            if self.stopped():
                                url_handle.close()
                                return
                    print("Download finished")
                    import zipfile
                    with zipfile.ZipFile(temp_zip_path) as zf:
                        print("Extracting zip to", os.path.join(user_preferences.global_dir, tcom.passargs['asset type'].lower()))
                        zf.extractall(os.path.join(user_preferences.global_dir, tcom.passargs['asset type'].lower()))

                except TimeoutError as error:
                    print("TimeoutError error: Could not download " + filename)
                    print(error)
                except urllib.error.URLError as error:
                    print("Could not download: " + filename)

                finally:
                    tcom.finished = True


class ThreadCom:  # object passed to threads to read background process stdout info
    def __init__(self):
        self.file_size = 1000000000000000  # property that gets written to.
        self.downloaded = 0
        self.progress = 0.0
        self.finished = False
        self.passargs = {}


def link_asset(context, asset, location, rotation):
    user_preferences = get_addon_preferences(context)

    filename = asset["url"]
    filepath = os.path.join(user_preferences.global_dir, "model", splitext(filename)[0] + '.blend')

    scene = context.scene
    link_model = (scene.luxcoreOL.model.append_method == 'LINK_COLLECTION')

    with bpy.data.libraries.load(filepath, link=link_model) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects]

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
            if obj.data != None:
                obj.data.make_local()
            parent = obj
            while parent.parent != None:
                parent = parent.parent

            if parent != main_object:
                parent.parent = main_object
                parent.matrix_parent_inverse = main_object.matrix_world.inverted() @ Matrix.Translation(-1*bbox_center)

        # Add objects to asset collection
        col.objects.link(obj)
        compatibility.run()


def append_material(context, asset, target_object, target_slot):
    if target_object == '':
        return

    user_preferences = get_addon_preferences(context)

    filename = asset["url"]
    filepath = os.path.join(user_preferences.global_dir, "material", splitext(filename)[0] + '.blend')

    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.materials = [name for name in data_from.materials if
                             name == asset["name"] or name == asset["name"].replace(" ", "_")]

    if len(data_to.materials) == 1:
        # print(target_object, target_slot, data_to.materials[0].name)
        if len(bpy.data.objects[target_object].material_slots) == 0:
            bpy.data.objects[target_object].data.materials.append(data_to.materials[0])
        else:
            if bpy.data.objects[target_object].library == None:
                bpy.data.objects[target_object].material_slots[target_slot].material = data_to.materials[0]
        compatibility.run()
    else:
        print('Error in material asset file ' + splitext(filename)[0] + '.blend' + ': Asset name does not match material name.')


def load_asset(context, asset, location, rotation, target_object, target_slot):
    user_preferences = get_addon_preferences(context)

    ui_props = context.scene.luxcoreOL.ui

    #TODO: write method for this as it is used serveral times
    if ui_props.asset_type == 'SCENE':
        filename = asset["url"]
        filepath = os.path.join(user_preferences.global_dir, "model", splitext(filename)[0] + '.blend')
    else:
        filename = asset["url"]
        filepath = os.path.join(user_preferences.global_dir, ui_props.asset_type.lower(), splitext(filename)[0] + '.blend')

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
        download_file(ui_props.asset_type, asset, location, rotation, target_object, target_slot)
    else:
        if ui_props.asset_type == 'MATERIAL':
            append_material(context, asset, target_object, target_slot)
        else:
            link_asset(context, asset, location, rotation)


def get_search_props(context):
    scene = context.scene
    if scene is None:
        return
    ui_props = scene.luxcoreOL.ui
    props = None

    if ui_props.asset_type == 'MODEL':
        if not 'assets' in scene.luxcoreOL.model:
            return
        props = scene.luxcoreOL.model['assets']
    if ui_props.asset_type == 'SCENE':
        if not 'assets' in scene.luxcoreOL.scene:
            return
        props = scene.luxcoreOL.scene['assets']
    if ui_props.asset_type == 'MATERIAL':
        if not 'assets' in scene.luxcoreOL.material:
            return
        props = scene.luxcoreOL.material['assets']

    # if ui_props.asset_type == 'TEXTURE':
    #     if not hasattr(scene.luxcoreOL.texture, 'assets'):
    #         return
    #     props = scene.luxcoreOL.texture['assets']

    # if ui_props.asset_type == 'BRUSH':
    #     if not hasattr(scene.luxcoreOL, 'brush'):
    #         return
    #     props = scene.luxcoreOL.brush['assets']
    return props


def get_default_directory():
    from os.path import expanduser
    home = expanduser("~")
    return home + os.sep + 'LuxCoreOnlineLibrary_data'


def get_scene_id():
    '''gets scene id and possibly also generates a new one'''
    bpy.context.scene['uuid'] = bpy.context.scene.get('uuid', str(uuid.uuid4()))
    return bpy.context.scene['uuid']


def download_thumbnail(self, context, asset):
    ui_props = context.scene.luxcoreOL.ui

    tcom = is_downloading(asset)
    if tcom is None:
        tcom = ThreadCom()
        tcom.passargs['thumbnail'] = True
        tcom.passargs['asset type'] = ui_props.asset_type

        downloadthread = Downloader(asset, tcom)

        download_threads.append([downloadthread, asset, tcom])
        bpy.app.timers.register(timer_update)

    return True


def get_thumbnail(imagename):
    # Prepend a dot so the image is hidden to users, e.g. in Blender's search
    imagename_blender = '.' + imagename

    img = bpy.data.images.get(imagename_blender)

    if img is None:
        addon_base_dir = dirname(dirname(dirname(__file__)))
        path = os.path.join(addon_base_dir, 'thumbnails', imagename)

        img = bpy.data.images.load(path)
        img.name = imagename_blender

        if bpy.app.version < (2, 83, 0):
            # Needed in old Blender versions so the images are not too dark
            img.colorspace_settings.name = 'Linear'

    return img


def clean_previmg(fullsize=False):
    if not fullsize:
        for img in [img for img in bpy.data.images if '.LOL_preview' in img.name]:
            if img.users == 0:
                bpy.data.images.remove(img)
    else:
        for img in [img for img in bpy.data.images if '.LOL_full_preview' in img.name]:
            if img.users == 0:
                bpy.data.images.remove(img)


def load_previews(context, asset_type):
    name = basename(dirname(dirname(dirname(__file__))))
    user_preferences = context.preferences.addons[name].preferences

    if asset_type == 'MODEL':
        assets = context.scene.luxcoreOL.model['assets']
    elif asset_type == 'SCENE':
        assets = context.scene.luxcoreOL.scene['assets']
    elif asset_type == 'MATERIAL':
        assets = context.scene.luxcoreOL.material['assets']

    clean_previmg()
    if assets is not None and len(assets) != 0:
        for asset in assets:
            if asset_type == 'MATERIAL':
                imagename = asset['name'].replace(" ", "_") + '.jpg'
            else:
                imagename = splitext(asset['url'])[0] + '.jpg'

            tpath_full = join(user_preferences.global_dir, asset_type, 'preview', 'full', imagename)
            tpath = join(user_preferences.global_dir, asset_type, 'preview', imagename)

            if os.path.exists(tpath_full) and os.path.getsize(tpath_full) > 0 and \
                    os.path.exists(tpath) and os.path.getsize(tpath) > 0:
                img = bpy.data.images.load(tpath)
                img.name = '.LOL_preview'

                asset["thumbnail"] = img

                if bpy.app.version < (2, 83, 0):
                    # Needed in old Blender versions so the images are not too dark
                    img.colorspace_settings.name = 'Linear'
            else:
                if os.path.exists(tpath) and os.path.getsize(tpath) > 0:
                    print('Copy and downscale: ', imagename)
                    img = bpy.data.images.load(tpath)
                    if img.size == (128, 128):
                        img.name = '.LOL_preview'
                    else:
                        from shutil import copyfile
                        copyfile(tpath, tpath_full)
                        img = bpy.data.images.load(tpath)
                        img.scale(128, 128)
                        img.save()
                        bpy.data.images.remove(img)

                        asset['thumbnail'] = bpy.data.images.load(tpath)
                        asset['thumbnail'].name = '.LOL_preview'



                rootdir = dirname(dirname(dirname(__file__)))
                path = join(rootdir, 'thumbnails', 'thumbnail_notready.jpg')
                img = bpy.data.images.load(path)
                img.name = '.LOL_preview'

                if bpy.app.version < (2, 83, 0):
                    # Needed in old Blender versions so the images are not too dark
                    img.colorspace_settings.name = 'Linear'

                asset["thumbnail"] = img
                if not asset['local']:
                    download_thumbnail(None, context, asset)