
""" Utility functions for our operators """

def make_nodetree_name(material_name):
    return "Nodes_" + material_name


def poll_volume(context):
    # Volume node trees are attached to a material output node
    if not hasattr(context, "node"):
        return False
    return context.node and not context.node.id_data.library


def poll_object(context):
    return context.object and not context.object.library


def poll_material(context):
        if not hasattr(context, "material"):
            return False
        return context.material and not context.material.library


def init_mat_node_tree(node_tree):
    # Seems like we still need this.
    # User counting does not work reliably with Python PointerProperty.
    # Sometimes, the material this tree is linked to is not counted as user.
    node_tree.use_fake_user = True

    nodes = node_tree.nodes

    output = nodes.new("LuxCoreNodeMatOutput")
    output.location = 300, 200
    output.select = False

    matte = nodes.new("LuxCoreNodeMatMatte")
    matte.location = 50, 200

    node_tree.links.new(matte.outputs[0], output.inputs[0])


def init_tex_node_tree(node_tree):
    # Seems like we still need this.
    # User counting does not work reliably with Python PointerProperty.
    # Sometimes, the material this tree is linked to is not counted as user.
    node_tree.use_fake_user = True

    nodes = node_tree.nodes

    output = nodes.new("LuxCoreNodeTexOutput")
    output.location = 300, 200
    output.select = False


def init_vol_node_tree(node_tree):
    # Seems like we still need this.
    # User counting does not work reliably with Python PointerProperty.
    # Sometimes, the material this tree is linked to is not counted as user.
    node_tree.use_fake_user = True

    nodes = node_tree.nodes

    output = nodes.new("LuxCoreNodeVolOutput")
    output.location = 300, 200
    output.select = False

    clear = nodes.new("LuxCoreNodeVolClear")
    clear.location = 50, 200

    node_tree.links.new(clear.outputs[0], output.inputs[0])
