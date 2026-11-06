import bpy
from bpy.app.handlers import persistent

@persistent
def handler(scene):
    # If material name was changed, rename the node tree, too.
    for mat in bpy.data.materials:
        if mat.library:
            # Linked materials are read-only from this file, renaming their node tree would fail
            continue

        node_tree = mat.luxcore.node_tree

        if node_tree and not node_tree.library and node_tree.name != mat.name:
            node_tree.name = mat.name
