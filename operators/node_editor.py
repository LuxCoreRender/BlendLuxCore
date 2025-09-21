import bpy
from mathutils import Vector
from .. import utils
from ..utils import node as utils_node
from ..utils.node import get_active_output, OUTPUT_MAP
from ..nodes.sockets import (
    LuxCoreSocketColor, LuxCoreSocketFloat, LuxCoreSocketVector,
    LuxCoreSocketMapping2D, LuxCoreSocketMapping3D,
)
from .utils import poll_node_tree

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
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_node_tree(context)

    def invoke(self, context, event):
        space = context.space_data
        node_tree = space.node_tree

        select_node = bpy.ops.node.select(location=(event.mouse_region_x, event.mouse_region_y), extend=False)
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
                    viewer_matte.location = active_output.location + Vector((0, 50))
                    viewer_matte.hide = True
                    viewer_matte[luxcore_viewer_mark] = True
                    sockets_to_link.append((viewer_matte.outputs[0], active_output.inputs["Material"]))

                    viewer_emission = node_tree.nodes.new("LuxCoreNodeMatEmission")
                    viewer_emission.location = active_output.location + Vector((0, 80))
                    viewer_emission.hide = True
                    viewer_emission[luxcore_viewer_mark] = True
                    viewer_emission.dls_type = "DISABLED"
                    sockets_to_link.append((viewer_emission.outputs[0], viewer_matte.inputs["Emission"]))
                    viewer_emission.gain = _calc_emission_viewer_gain(context)

                    viewer_node = node_tree.nodes.new("NodeReroute")
                    viewer_node.location = active_output.location + Vector((-10, 55))
                    viewer_node[luxcore_viewer_mark] = True
                    viewer_node[luxcore_viewer_reroute_mark] = True
                    # Diffuse color for albedo preview (material shading mode), emission for regular viewport render
                    sockets_to_link.append((viewer_node.outputs[0], viewer_matte.inputs["Diffuse Color"]))
                    sockets_to_link.append((viewer_node.outputs[0], viewer_emission.inputs["Color"]))

                target_socket = viewer_node.inputs[0]
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


class LUXCORE_OT_mute_node(bpy.types.Operator):
    bl_idname = "luxcore.mute_node"
    bl_label = "Mute Node"
    bl_description = "Toggle mute state of all selected nodes"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_node_tree(context)

    def invoke(self, context, event):
        space = context.space_data
        node_tree = space.node_tree

        for node in node_tree.nodes:
            if node.select and node.bl_idname not in OUTPUT_MAP.values():
                node.mute = not node.mute

        node_tree.update()
        return {"FINISHED"}


class LUXCORE_OT_node_editor_add_image(bpy.types.Operator):
    bl_idname = "luxcore.node_editor_add_image"
    bl_label = "Add Image"
    bl_description = "Add image and mapping node to selected nodes"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_node_tree(context)

    def invoke(self, context, event):
        space = context.space_data
        node_tree = space.node_tree
        
        allowed_inputs = {
            LuxCoreSocketColor, LuxCoreSocketFloat,
            LuxCoreSocketMapping2D, LuxCoreSocketMapping3D,
        }

        for node in [node for node in node_tree.nodes if node.select]:
            unlinked_input = None
            for socket in node.inputs:
                if not socket.is_linked and _is_allowed_input(allowed_inputs, socket):
                    unlinked_input = socket
                    break
            if not unlinked_input:
                continue

            def is_2d_socket(socket):
                return isinstance(unlinked_input, LuxCoreSocketMapping2D)
            def is_3d_socket(socket):
                return isinstance(unlinked_input, LuxCoreSocketMapping3D)

            if is_2d_socket(unlinked_input) or is_3d_socket(unlinked_input):
                tex_node = node
            else:
                tex_node = node_tree.nodes.new("LuxCoreNodeTexImagemap")
                tex_node.location = node.location + Vector((-240, 0))
                node_tree.links.new(tex_node.outputs["Color"], unlinked_input)
                unlinked_input = tex_node.inputs[0]

            if is_2d_socket(unlinked_input):
                mapping_node = node_tree.nodes.new("LuxCoreNodeTexMapping2D")
                offset = Vector((-200, 0))
            else:
                assert is_3d_socket(unlinked_input)
                mapping_node = node_tree.nodes.new("LuxCoreNodeTexMapping3D")
                offset = Vector((-300, 0))

            mapping_node.location = tex_node.location + offset
            node_tree.links.new(mapping_node.outputs[0], unlinked_input)
            
            node.select = False

        # node_tree.update()
        return {"FINISHED"}
