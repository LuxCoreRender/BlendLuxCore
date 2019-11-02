import bpy
from bpy.app.handlers import persistent
from ..utils import node as utils_node
from ..utils import openVDB_sequence_resolve_all
from ..utils import clamp

@persistent
def handler(scene):
    for node_tree in bpy.data.node_groups:
        for node in utils_node.find_nodes(node_tree, "LuxCoreNodeTexImagemap"):
            if node.image and node.image.source == "SEQUENCE":
                # Force a viewport update
                node.image = node.image

        for node in utils_node.find_nodes(node_tree, "LuxCoreNodeTexSmoke"):
            if node.domain:
                node.domain = node.domain

        if utils_node.find_nodes(node_tree, "LuxCoreNodeTexOpenVDB"):
            for n in node_tree.nodes:
                if n.name.split('.')[0] == "Material Output" and n.active:
                    node_tree.links.new(n.inputs["Material"], n.inputs["Material"].links[0].from_socket)

