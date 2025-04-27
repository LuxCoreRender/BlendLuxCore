import bpy
from .node import find_nodes
from ..nodes import TREE_TYPES
from ..nodes.base import ThinFilmCoating


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
        update_smoke_mantaflow_simulation(node_tree)
        update_mat_output_add_shape_input(node_tree)
        update_glass_disney_add_film_sockets(node_tree)
        update_invert_add_maximum_input(node_tree)
        update_brick_texture(node_tree)

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
        node_id = node.inputs.find("IOR")
        if node_id == -1:
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
        node_id = node.inputs.find("Asymmetry")
        asymmetry_socket = node.inputs[node_id]
        if asymmetry_socket.bl_idname == "NodeSocketUndefined":
            node.inputs.remove(asymmetry_socket)
            node.add_input("LuxCoreSocketVolumeAsymmetry", "Asymmetry", (0, 0, 0))
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_colormix_remove_min_max_sockets(node_tree):
    # commit 432b1ba020b07f46758fd19b4b3af91cca0c90ff

    for node in find_nodes(node_tree, "LuxCoreNodeTexColorMix", False):
        if node.mode == "clamp" and "Min" in node.inputs and "Max" in node.inputs:
            id_min = node.inputs.find("Min")
            socket_min = node.inputs[id_min]
            id_max = node.inputs.find("Max")
            socket_max = node.inputs[id_max]
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
            node_id = node.inputs.find("Gamma")
            socket_gamma = node.inputs[node_id]
            node.gamma = socket_gamma.default_value
            node.inputs.remove(socket_gamma)
            updated = True

        if "Brightness" in node.inputs:
            node_id = node.inputs.find("Brightness")
            socket_brightness = node.inputs[node_id]
            node.brightness = socket_brightness.default_value
            node.inputs.remove(socket_brightness)
            updated = True

        if updated:
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_cloth_remove_repeat_sockets(node_tree):
    # commit ec3fccdccb3e4c95a4230df8b38f6494bb8e4583

    for node in find_nodes(node_tree, "LuxCoreNodeMatCloth", False):
        if "Repeat U" in node.inputs and "Repeat V" in node.inputs:
            node_id = node.inputs.find("Repeat U")
            socket_repeat_u = node.inputs[node_id]
            node_id = node.inputs.find("Repeat V")
            socket_repeat_v = node.inputs[node_id]
            node.repeat_u = socket_repeat_u.default_value
            node.repeat_v = socket_repeat_v.default_value
            node.inputs.remove(socket_repeat_u)
            node.inputs.remove(socket_repeat_v)
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_imagemap_add_alpha_output(node_tree):
    # commit 09f23b0d758bce9383a0fa8c64ccbeb73706bccf

    for node in find_nodes(node_tree, "LuxCoreNodeTexImagemap", False):
        node_id = node.outputs.find("Alpha")
        if node_id == -1:
            node.outputs.new("LuxCoreSocketFloatUnbounded", "Alpha")
            print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_smoke_multiple_output_channels(node_tree):
    # commit 204c96ec0d7f5d8d0dbdd183da61b69718aa1747

    for node in find_nodes(node_tree, "LuxCoreNodeTexSmoke", False):
        node_id = node.outputs.find("density")
        if node_id != -1:
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

        node_id = node.outputs.find("Color")
        node.outputs.remove(node.outputs[node_id])
        node_id = node.outputs.find("Value")
        node.outputs.remove(node.outputs[node_id])

        print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))


def update_smoke_mantaflow_simulation(node_tree):
    # commit 6184e20b1fe2a5766c7ea89c4588641909bc9454
    for node in find_nodes(node_tree, "LuxCoreNodeTexSmoke", False):
        node_id = node.outputs.find("flame")
        if node_id != -1:
            continue
        # Copy current output sockets for reconnection after update
        old_sockets = {}
        for e in node.outputs:
            links = []
            for link in e.links:
                links.append(link.to_socket)
            if e.name == 'fire':
                old_sockets['flame'] = links.copy()
            else:
                old_sockets[e.name] = links.copy()

        node_id = node.outputs.find("density")
        node.outputs.remove(node.outputs[node_id])
        node_id = node.outputs.find("fire")
        node.outputs.remove(node.outputs[node_id])
        node_id = node.outputs.find("heat")
        node.outputs.remove(node.outputs[node_id])
        node_id = node.outputs.find("color")
        node.outputs.remove(node.outputs[node_id])
        node_id = node.outputs.find("velocity")
        node.outputs.remove(node.outputs[node_id])

        node.outputs.new("LuxCoreSocketFloatPositive", "density")
        node.outputs.new("LuxCoreSocketFloatPositive", "flame")
        node.outputs.new("LuxCoreSocketFloatPositive", "heat")
        node.outputs.new("LuxCoreSocketFloatPositive", "temperature")
        node.outputs.new("LuxCoreSocketColor", "color")
        node.outputs.new("LuxCoreSocketColor", "velocity")

        for output in node.outputs:
            try:
                for link in old_sockets[output.name]:
                    node_tree.links.new(output, link)
            except KeyError:
                pass

        print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))

def update_mat_output_add_shape_input(node_tree):
    # commit e20355a7567b22df4d05e8b303c98dbc697b9c08

    for node in find_nodes(node_tree, "LuxCoreNodeMatOutput", False):
        node_id = node.inputs.find("Shape")
        if node_id == -1:
            node.inputs.new("LuxCoreSocketShape", "Shape")
            print('Updated output node "%s" in tree %s to new version' % (node.name, node_tree.name))


def update_glass_disney_add_film_sockets(node_tree):
    affected_nodes = find_nodes(node_tree, "LuxCoreNodeMatGlass", False)
    affected_nodes += find_nodes(node_tree, "LuxCoreNodeMatDisney", False)
    
    for node in affected_nodes:
        node_id = node.inputs.find(ThinFilmCoating.THICKNESS_NAME)
        if node_id != -1:
            continue
        
        if node.bl_idname == "LuxCoreNodeMatDisney":
            node.add_input("LuxCoreSocketFloat0to1", "Film Amount", 1, enabled=False)
        
        ThinFilmCoating.init(node)
        print('Updated node "%s" in tree %s to new version' % (node.name, node_tree.name))


def update_invert_add_maximum_input(node_tree):
    # commit 4fcce04f9c51dce990e2480810265c1f1b13c8c5

    for node in find_nodes(node_tree, "LuxCoreNodeTexInvert", False):
        node_id = node.inputs.find("Maximum")
        if node_id == -1:
            node.add_input("LuxCoreSocketFloatPositive", "Maximum", 1)
            print('Updated invert node "%s" in tree %s to new version' % (node.name, node_tree.name))


def update_brick_texture(node_tree):
    # commit a4aff62a1608f95fc7bd7fbbdf19f5ab444e0d6b

    for node in find_nodes(node_tree, "LuxCoreNodeTexBrick", False):
        node_id = node.inputs.find("Brick Color 1")
        if node_id != -1:
            continue

        node_id = node.inputs.find("bricktex")
        node.inputs[node_id].name = "Brick Color 1"
        node_id = node.inputs.find("mortartex")
        node.inputs[node_id].name = "Mortar Color"
        node_id = node.inputs.find("brickmodtex")
        node.inputs[node_id].name = "Brick Color 2"

        print('Updated %s node "%s" in tree "%s" to new version' % (node.bl_idname, node.name, node_tree.name))
