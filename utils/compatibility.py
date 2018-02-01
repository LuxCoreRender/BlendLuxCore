import bpy
from .node import find_nodes


"""
Contains functions that are executed when a .blend is loaded. 
They ensure backwards compatibility, 
e.g. replace old nodes with updated ones when socket names change.
"""


def run():
    update_output_nodes_volume_change()


def update_output_nodes_volume_change():
    # commit 3078719a9a33a7e2a798965294463dce6c8b7749

    for node_tree in bpy.data.node_groups:
        if node_tree.library:
            continue

        for old_output in find_nodes(node_tree, "LuxCoreNodeMatOutput"):
            if "Interior Volume" in old_output.inputs:
                continue

            from_node = old_output.inputs[0].links[0].from_node

            new_out = node_tree.nodes.new("LuxCoreNodeMatOutput")
            new_out.location = old_output.location
            node_tree.links.new(from_node.outputs[0], new_out.inputs[0])

            # Move the old volume node tree PointerProperties into Pointer nodes
            try:
                interior = old_output["interior_volume"]

                if interior:
                    volume_pointer = node_tree.nodes.new("LuxCoreNodeTreePointer")
                    volume_pointer.node_tree = interior
                    volume_pointer.location = (new_out.location.x - 250, new_out.location.y - 100)
                    node_tree.links.new(volume_pointer.outputs["Volume"], new_out.inputs["Interior Volume"])
                    print("linked interior", node_tree.name)

                exterior = old_output["exterior_volume"]

                if exterior:
                    volume_pointer = node_tree.nodes.new("LuxCoreNodeTreePointer")
                    volume_pointer.node_tree = exterior
                    volume_pointer.location = (new_out.location.x - 250, new_out.location.y - 250)
                    node_tree.links.new(volume_pointer.outputs["Volume"], new_out.inputs["Exterior Volume"])
            except KeyError:
                pass

            print("Updated output node %s in tree %s to new version" % (old_output.name, node_tree.name))
            node_tree.nodes.remove(old_output)
