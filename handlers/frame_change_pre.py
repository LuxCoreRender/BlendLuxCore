import bpy
from bpy.app.handlers import persistent
from ..utils import node as utils_node
from ..utils import openVDB_sequence_resolve_all
from ..utils import clamp

RELEVANT_NODES = {"LuxCoreNodeTexImagemap", "LuxCoreNodeTexOpenVDB", "LuxCoreNodeTexTimeInfo"}

# Flags that save us from having to iterate all node trees when no related nodes are used (the common case).
# Set in relevant node export methods, reset when new .blend is loaded in load_post.
have_to_check_node_trees = False

# Important: Since this function is executed on every frame, even milliseconds of processin time in here will
# bring down the frame rate of animations considerably. Always assume the worst case: A big scene with many
# materials and complex node trees, and optimize for it.
@persistent
def handler(scene):
    global have_to_check_node_trees

    if not have_to_check_node_trees or scene.render.engine != "LUXCORE":
        return

    found_relevant_node = False
    for mat in bpy.data.materials:
        if not mat.luxcore.node_tree:
            continue

        if utils_node.has_nodes_multi(mat.luxcore.node_tree, RELEVANT_NODES, True):
            found_relevant_node = True
            # Force a viewport update
            mat.diffuse_color = mat.diffuse_color

    have_to_check_node_trees = found_relevant_node

    # TODO we are not handling area lights with image sequence textures right now
    #  because I can't think of a check with good performance in large scenes.


    # This is what I would like to do, but it does not work if the node tree is not selected in any node editor.
    # Also, users of edited node trees are not flagged as updated (e.g. materials, area lights, camera) which
    # is a Blender bug/limitation.
    #
    # from ..nodes import TREE_TYPES
    # for node_tree in bpy.data.node_groups:
    #     if node_tree.bl_idname not in TREE_TYPES:
    #         continue
    #
    #     for node in utils_node.find_nodes(node_tree, "LuxCoreNodeTexImagemap"):
    #         if node.image and node.image.source == "SEQUENCE":
    #             # Force a viewport update
    #             node.image = node.image
    #             # node_tree.update_tag()  # Does not work
