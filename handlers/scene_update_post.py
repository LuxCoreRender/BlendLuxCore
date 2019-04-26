import os
from time import time
import bpy
from bpy.app.handlers import persistent
from .. import utils

# We only sync material and node tree names every second to reduce CPU load
NAME_UPDATE_INTERVAL = 1  # seconds
last_name_update = time()


@persistent
def handler(scene):
    photongi_file = utils.get_abspath(scene.luxcore.config.photongi.file_path, scene.library)
    if os.path.isfile(photongi_file):
        # We have a cache, check if it's dirty
        dirty = False
        reason = []

        if bpy.data.meshes.is_updated or bpy.data.lamps.is_updated or bpy.data.curves.is_updated:
            dirty = True
            if bpy.data.meshes.is_updated:
                reason.append("meshes")
            if bpy.data.lamps.is_updated:
                reason.append("lamps")
            if bpy.data.curves.is_updated:
                reason.append("curves")

        # TODO check PhotonGI settings for changes

        if bpy.data.objects.is_updated:
            for obj in bpy.data.objects:
                if obj.is_updated and obj != scene.camera:
                    dirty = True
                    reason.append("Obj: " + obj.name)
                    break

        if dirty:
            print("Dirt reason:", " | ".join(reason))
            print("Deleting dirty cache:", os.path.basename(photongi_file))
            os.remove(photongi_file)

    global last_name_update
    if time() - last_name_update < NAME_UPDATE_INTERVAL:
        return
    last_name_update = time()

    # If material name was changed, rename the node tree, too.
    # Note that bpy.data.materials.is_updated is always False here
    # so we can't use it as fast check.
    for mat in bpy.data.materials:
        node_tree = mat.luxcore.node_tree

        if node_tree and node_tree.name != mat.name:
            node_tree.name = mat.name
