import bpy
import mathutils
from .. import utils
from ..utils import node as utils_node
from ..nodes import TREE_TYPES
from ..nodes.output import get_active_output

luxcore_viewer_reroute_mark = "luxcore_viewer_reroute"
luxcore_viewer_mark = "luxcore_viewer"


def _remove_all_viewers(node_tree):
    for node in reversed(node_tree.nodes):
        if luxcore_viewer_mark in node:
            node_tree.nodes.remove(node)


def _calc_emission_viewer_gain(context):
    # Compensate for tonemapping and color management
    gain = 1
    if utils.is_valid_camera(context.scene.camera):
        tonemapper = context.scene.camera.data.luxcore.imagepipeline.tonemapper
        if tonemapper.enabled and tonemapper.type == "TONEMAP_LINEAR":
            gain = 1 / tonemapper.linear_scale
    gain /= pow(2, (context.scene.view_settings.exposure))
    return gain


def _is_allowed_input(allowed_inputs, socket):
    for allowed_class in allowed_inputs:
        if isinstance(socket, allowed_class):
            return True
    return False


class LUXCORE_OT_node_editor_viewer(bpy.types.Operator):
    bl_idname = "luxcore.node_editor_viewer"
    bl_label = "Insert Viewer"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if space.type != 'NODE_EDITOR':
            return False
        return space.node_tree and space.node_tree.bl_idname in TREE_TYPES

    def invoke(self, context, event):
        space = context.space_data
        node_tree = space.node_tree

        select_node = bpy.ops.node.select(mouse_x=event.mouse_region_x, mouse_y=event.mouse_region_y, extend=False)
        if 'FINISHED' not in select_node:
            return {'CANCELLED'}

        active_output = get_active_output(node_tree)
        if not active_output:
            return {'CANCELLED'}

        viewer_node = None
        for node in node_tree.nodes:
            if luxcore_viewer_reroute_mark in node:
                viewer_node = node
                break

        active_node = node_tree.nodes.active
        target_socket = None
        allowed_inputs = set()
        sockets_to_link = []

        if node_tree.bl_idname == "luxcore_material_nodes":
            if active_node.bl_idname.startswith("LuxCoreNodeMat"):
                target_socket = active_output.inputs["Material"]
                allowed_inputs = target_socket.allowed_inputs
                if viewer_node:
                    _remove_all_viewers(node_tree)
            elif active_node.bl_idname.startswith("LuxCoreNodeShape"):
                target_socket = active_output.inputs["Shape"]
                allowed_inputs = target_socket.allowed_inputs
                if viewer_node:
                    _remove_all_viewers(node_tree)
            elif active_node.bl_idname.startswith("LuxCoreNodeTex"):
                if viewer_node:
                    # Existing viewer setup, find the emission node and update the gain
                    for node in node_tree.nodes:
                        if luxcore_viewer_mark in node and node.bl_idname == "LuxCoreNodeMatEmission":
                            node.gain = _calc_emission_viewer_gain(context)
                            break
                else:
                    viewer_matte = node_tree.nodes.new("LuxCoreNodeMatMatte")
                    viewer_matte.location = active_output.location + mathutils.Vector((0, 50))
                    viewer_matte.hide = True
                    viewer_matte[luxcore_viewer_mark] = True
                    sockets_to_link.append((viewer_matte.outputs[0], active_output.inputs["Material"]))

                    viewer_emission = node_tree.nodes.new("LuxCoreNodeMatEmission")
                    viewer_emission.location = active_output.location + mathutils.Vector((0, 80))
                    viewer_emission.hide = True
                    viewer_emission[luxcore_viewer_mark] = True
                    viewer_emission.dls_type = "DISABLED"
                    sockets_to_link.append((viewer_emission.outputs[0], viewer_matte.inputs["Emission"]))
                    viewer_emission.gain = _calc_emission_viewer_gain(context)

                    viewer_node = node_tree.nodes.new("NodeReroute")
                    viewer_node.location = active_output.location + mathutils.Vector((-10, 55))
                    viewer_node[luxcore_viewer_mark] = True
                    viewer_node[luxcore_viewer_reroute_mark] = True
                    # Diffuse color for albedo preview (material shading mode), emission for regular viewport render
                    sockets_to_link.append((viewer_node.outputs[0], viewer_matte.inputs["Diffuse Color"]))
                    sockets_to_link.append((viewer_node.outputs[0], viewer_emission.inputs["Color"]))

                target_socket = viewer_node.inputs[0]
                from ..nodes.sockets import LuxCoreSocketColor, LuxCoreSocketFloat, LuxCoreSocketVector
                allowed_inputs = {LuxCoreSocketColor, LuxCoreSocketFloat, LuxCoreSocketVector}
        elif node_tree.bl_idname == "luxcore_texture_nodes":
            target_socket = active_output.inputs["Color"]
            allowed_inputs = target_socket.allowed_inputs
        elif node_tree.bl_idname == "luxcore_volume_nodes":
            target_socket = active_output.inputs["Volume"]
            allowed_inputs = target_socket.allowed_inputs

        if not target_socket:
            return {"CANCELLED"}

        visible_output_socket_indices = [i for i, output in enumerate(active_node.outputs)
                                         if output.enabled and _is_allowed_input(allowed_inputs, output)]
        if not visible_output_socket_indices:
            _remove_all_viewers(node_tree)
            return {"CANCELLED"}
        active_socket_index = 0

        old_link = utils_node.get_link(target_socket)
        if old_link:
            old_index = old_link.from_node.outputs.find(old_link.from_socket.name)
            active_socket_index = old_index + 1

        if active_socket_index >= len(visible_output_socket_indices):
            active_socket_index = 0

        active_output_socket = active_node.outputs[visible_output_socket_indices[active_socket_index]]
        sockets_to_link.append((active_output_socket, target_socket))
        for output_socket, input_socket in sockets_to_link:
            node_tree.links.new(output_socket, input_socket)
        return {"FINISHED"}
