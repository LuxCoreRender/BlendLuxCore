import bpy
from bpy.app.handlers import persistent
from ..utils import node as utils_node
from ..utils import openVDB_sequence_resolve_all
from ..utils import clamp

# Flag that saves us from having to iterate all node trees when no image sequences are used (the common case).
# Set in image node export method, reset when new .blend is loaded in load_post.
using_image_sequences = False

# Flag that saves us from having to iterate all node trees when no image sequences are used (the common case).
# Set in openVDB node export method, reset when new .blend is loaded in load_post.
using_smoke_sequences = False


@persistent
def handler(scene):
    global using_image_sequences
    global using_smoke_sequences

    if not (using_image_sequences or using_smoke_sequences) or scene.render.engine != "LUXCORE":
        return

    found_image_sequence = False
    found_smoke_sequence = False
    for mat in bpy.data.materials:
        if not mat.luxcore.node_tree:
            continue

        if utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexOpenVDB") or \
                utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexSmoke"):
            found_smoke_sequence = True
            for n in mat.luxcore.node_tree.nodes:
                if n.active and n.name.split('.')[0] == "Material Output":
                    # Force a viewport update
                    mat.luxcore.node_tree.links.new(n.inputs["Material"], n.inputs["Material"].links[0].from_socket)

        for node in utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexImagemap"):
            if node.image and node.image.source == "SEQUENCE":
                found_image_sequence = True
                # Force a viewport update
                mat.diffuse_color = mat.diffuse_color
                break

    using_image_sequences = found_image_sequence
    using_smoke_sequences = found_smoke_sequence

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
