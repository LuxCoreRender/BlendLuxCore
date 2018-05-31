from time import time
import bpy
from bpy.app.handlers import persistent

# We only sync material and node tree names every second to reduce CPU load
NAME_UPDATE_INTERVAL = 1  # seconds
last_name_update = time()


@persistent
def handler(scene):
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
