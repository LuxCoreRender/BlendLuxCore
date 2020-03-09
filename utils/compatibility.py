import bpy
from .node import find_nodes
from ..nodes import TREE_TYPES


"""
Contains functions that ensure backwards compatibility, 
e.g. replace old nodes with updated ones when socket names change.
"""


def run():
    for node_tree in bpy.data.node_groups:
        if node_tree.bl_idname not in TREE_TYPES:
            continue

        update_mat_output_volume_change(node_tree)
        update_glossy_ior_change(node_tree)
        update_volume_asymmetry_change(node_tree)
        update_colormix_remove_min_max_sockets(node_tree)
        update_imagemap_remove_gamma_brightness_sockets(node_tree)
        update_cloth_remove_repeat_sockets(node_tree)
        update_imagemap_add_alpha_output(node_tree)
        update_smoke_multiple_output_channels(node_tree)

    for scene in bpy.data.scenes:
        config = scene.luxcore.config
        # Reworked after v2.2beta4, DLSC is no longer part of the light strategy enum, but a separate checkbox.
        # Commit: 87ef293cdac2011da28365941414f88ff2658903
        if config.light_strategy == "":
            # It was probably DLS_CACHE. We have no way to find out,
            # but that is the only entry that was ever removed.
            # Restore the default here and enable the new DLSC BoolProperty
            config.light_strategy = "LOG_POWER"
            config.dls_cache.enabled = True

    # Since commit 28a45283c249085ec1ae8ff38665f6d3655bb998 we use the Cycles DOF properties instead
    # of our own. Apply the old properties if an old scene uses them.
    for camera in bpy.data.cameras:
        if camera.luxcore.use_dof:
            camera.dof.use_dof = True
            camera.dof.aperture_fstop = camera.luxcore.fstop
            camera.luxcore.use_dof = False


def update_mat_output_volume_change(node_tree):
    # commit 3078719a9a33a7e2a798965294463dce6c8b7749

    for old_output in find_nodes(node_tree, "LuxCoreNodeMatOutput", False):
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

        print('Updated output node "%s" in tree %s to new version' % (old_output.name, node_tree.name))
        node_tree.nodes.remove(old_output)


def update_glossy_ior_change(node_tree):
    # commit c3152dec8e0e07e676a60be56ba4578dbe297df6

    affected_nodes = find_nodes(node_tree, "LuxCoreNodeMatGlossy2", False)
    affected_nodes += find_nodes(node_tree, "LuxCoreNodeMatGlossyCoating", False)

    for node in affected_nodes:
        if "IOR" not in node.inputs:
            # Note: the IOR input will be at the very bottom, but at least the export works
            node.add_input("LuxCoreSocketIOR", "IOR", 1.5)
            node.inputs["IOR"].enabled = False
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_volume_asymmetry_change(node_tree):
    # commit 2387d1c300b5a1f6931592efcdd0574d243356e7

    if node_tree.bl_idname != "luxcore_volume_nodes":
        return

    affected_nodes = find_nodes(node_tree, "LuxCoreNodeVolHeterogeneous", False)
    affected_nodes += find_nodes(node_tree, "LuxCoreNodeVolHomogeneous", False)

    for node in affected_nodes:
        asymmetry_socket = node.inputs["Asymmetry"]
        if asymmetry_socket.bl_idname == "NodeSocketUndefined":
            node.inputs.remove(asymmetry_socket)
            node.add_input("LuxCoreSocketVolumeAsymmetry", "Asymmetry", (0, 0, 0))
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_colormix_remove_min_max_sockets(node_tree):
    # commit 432b1ba020b07f46758fd19b4b3af91cca0c90ff

    for node in find_nodes(node_tree, "LuxCoreNodeTexColorMix", False):
        if node.mode == "clamp" and "Min" in node.inputs and "Max" in node.inputs:
            socket_min = node.inputs["Min"]
            socket_max = node.inputs["Max"]
            node.mode_clamp_min = socket_min.default_value
            node.mode_clamp_max = socket_max.default_value
            node.inputs.remove(socket_min)
            node.inputs.remove(socket_max)
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_imagemap_remove_gamma_brightness_sockets(node_tree):
    # commit 428110b2c1bdbf8c54a54030939b3c76cb018644

    for node in find_nodes(node_tree, "LuxCoreNodeTexImagemap", False):
        updated = False
        if "Gamma" in node.inputs:
            socket_gamma = node.inputs["Gamma"]
            node.gamma = socket_gamma.default_value
            node.inputs.remove(socket_gamma)
            updated = True

        if "Brightness" in node.inputs:
            socket_brightness = node.inputs["Brightness"]
            node.brightness = socket_brightness.default_value
            node.inputs.remove(socket_brightness)
            updated = True

        if updated:
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_cloth_remove_repeat_sockets(node_tree):
    # commit ec3fccdccb3e4c95a4230df8b38f6494bb8e4583

    for node in find_nodes(node_tree, "LuxCoreNodeMatCloth", False):
        if "Repeat U" in node.inputs and "Repeat V" in node.inputs:
            socket_repeat_u = node.inputs["Repeat U"]
            socket_repeat_v = node.inputs["Repeat V"]
            node.repeat_u = socket_repeat_u.default_value
            node.repeat_v = socket_repeat_v.default_value
            node.inputs.remove(socket_repeat_u)
            node.inputs.remove(socket_repeat_v)
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_imagemap_add_alpha_output(node_tree):
    # commit 09f23b0d758bce9383a0fa8c64ccbeb73706bccf

    for node in find_nodes(node_tree, "LuxCoreNodeTexImagemap", False):
        if "Alpha" not in node.outputs:
            node.outputs.new("LuxCoreSocketFloatUnbounded", "Alpha")
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_smoke_multiple_output_channels(node_tree):
    # commit 204c96ec0d7f5d8d0dbdd183da61b69718aa1747

    for node in find_nodes(node_tree, "LuxCoreNodeTexSmoke", False):
        if "density" in node.outputs:
            continue

        node.outputs.new("LuxCoreSocketFloatPositive", "density")
        node.outputs.new("LuxCoreSocketFloatPositive", "fire")
        node.outputs.new("LuxCoreSocketFloatPositive", "heat")
        node.outputs.new("LuxCoreSocketColor", "color")
        node.outputs.new("LuxCoreSocketColor", "velocity")

        map_source_to_old_output_name = {
            "density": "Value",
            "fire": "Value",
            "heat": "Value",
            "color": "Color",
            "velocity": "Color",
        }
        old_output_name = map_source_to_old_output_name[node.source]
        new_output_name = node.source

        for link in node.outputs[old_output_name].links:
            node_tree.links.new(node.outputs[new_output_name], link.to_socket)

        node.outputs.remove(node.outputs["Color"])
        node.outputs.remove(node.outputs["Value"])

        print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))
