import bpy
from bpy.props import IntProperty
from ..utils import node as utils_node
from ..properties.lightgroups import MAX_LIGHTGROUPS, is_lightgroup_pass_name


class LUXCORE_OT_add_lightgroup(bpy.types.Operator):
    bl_idname = "luxcore.add_lightgroup"
    bl_label = "Add Light Group"
    bl_description = "Add a light group"
    bl_options = {"UNDO"}

    def execute(self, context):
        groups = context.scene.luxcore.lightgroups
        groups.add()
        return {"FINISHED"}


class LUXCORE_OT_remove_lightgroup(bpy.types.Operator):
    bl_idname = "luxcore.remove_lightgroup"
    bl_label = "Remove Light Group"
    bl_description = "Remove this light group"
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        groups = context.scene.luxcore.lightgroups
        groups.remove(self.index)
        return {"FINISHED"}


class LUXCORE_OT_select_objects_in_lightgroup(bpy.types.Operator):
    bl_idname = "luxcore.select_objects_in_lightgroup"
    bl_label = "Select Objects"
    bl_description = ("Select all objects that are affected by this light "
                      "group (lights and meshes with emissive material)\n"
                      "Selection will be added to the current selection")
    bl_options = {"UNDO"}

    index: IntProperty()

    def execute(self, context):
        group_name = context.scene.luxcore.lightgroups.custom[self.index].name
        relevant_node_types = {
            "LuxCoreNodeMatEmission",
            "LuxCoreNodeVolClear",
            "LuxCoreNodeVolHomogeneous",
            "LuxCoreNodeVolHeterogeneous",
        }

        # There are probably far less materials than objects in the scene
        materials_in_group = set()
        for mat in bpy.data.materials:
            node_tree = mat.luxcore.node_tree
            if not node_tree or mat.luxcore.use_cycles_nodes:
                continue

            for node in utils_node.find_nodes_multi(node_tree, relevant_node_types, follow_pointers=True):
                if node.lightgroup == group_name:
                    materials_in_group.add(mat)
                    break

        for obj in context.scene.objects:
            if obj.type == "LIGHT" and obj.data.luxcore.lightgroup == group_name:
                obj.select_set(True, view_layer=context.view_layer)
            else:
                for mat_slot in obj.material_slots:
                    if mat_slot.material in materials_in_group:
                        obj.select_set(True, view_layer=context.view_layer)
                        break

        return {"FINISHED"}


# Marks to find our node trees if they already exist
LUX_EDITOR_MARK = "luxcore_light_group_editor"
LUX_MIXER_MARK = "luxcore_light_group_mixer"
LUX_MIXER_INSTANCE_MARK = "luxcore_light_group_mixer_instance"
# Our node tree names
EDIT_LIGHT_GROUP_NAME = ".LightGroupEditor"
LIGHT_GROUP_MIXER_NAME = ".LightGroupMixer"


def create_editor():
    for node_tree in bpy.data.node_groups:
        if LUX_EDITOR_MARK in node_tree:
            return node_tree

    editor = bpy.data.node_groups.new(EDIT_LIGHT_GROUP_NAME, "CompositorNodeTree")
    editor[LUX_EDITOR_MARK] = True

    input_node = editor.nodes.new("NodeGroupInput")
    output_node = editor.nodes.new("NodeGroupOutput")
    editor.interface.new_socket(socket_type="NodeSocketColor", name="Light Group", in_out="INPUT")
    gain = editor.interface.new_socket(socket_type="NodeSocketFloat", name="Gain", in_out="INPUT")
    gain.default_value = 1
    gain.min_value = 0
    color = editor.interface.new_socket(socket_type="NodeSocketColor", name="Color", in_out="INPUT")
    color.default_value = (1, 1, 1, 1)
    editor.interface.new_socket(socket_type="NodeSocketColor", name="Image", in_out="OUTPUT")

    multiply_color = editor.nodes.new("CompositorNodeMixRGB")
    multiply_color.blend_type = "MULTIPLY"
    editor.links.new(input_node.outputs["Light Group"], multiply_color.inputs[1])
    editor.links.new(input_node.outputs["Color"], multiply_color.inputs[2])

    mix_gain = editor.nodes.new("CompositorNodeMixRGB")
    mix_gain.blend_type = "MIX"
    mix_gain.inputs[1].default_value = (0, 0, 0, 1)
    editor.links.new(input_node.outputs["Gain"], mix_gain.inputs[0])
    editor.links.new(multiply_color.outputs[0], mix_gain.inputs[2])

    editor.links.new(mix_gain.outputs[0], output_node.inputs[0])

    input_node.location = (-630, 90)
    output_node.location = (200, 60)
    multiply_color.location = (-320, -20)
    mix_gain.location = (-70, 110)
    return editor


# Index of first lightgroup-related socket after the ALBEDO and AVG_SHADING_NORMAL sockets
MIXER_SOCKET_INDEX_START = 2
# Amount of steps from one light group input socket to the next (stepping over gain, color etc.)
MIXER_SOCKET_INDEX_STEP = 3


def create_mixer(editor):
    for node_tree in bpy.data.node_groups:
        if LUX_MIXER_MARK in node_tree:
            return node_tree

    mixer = bpy.data.node_groups.new(LIGHT_GROUP_MIXER_NAME, "CompositorNodeTree")
    mixer[LUX_MIXER_MARK] = True

    input_node = mixer.nodes.new("NodeGroupInput")
    output_node = mixer.nodes.new("NodeGroupOutput")
    mixer.interface.new_socket(socket_type="NodeSocketColor", name="ALBEDO", in_out="INPUT")
    mixer.interface.new_socket(socket_type="NodeSocketVector", name="AVG_SHADING_NORMAL", in_out="INPUT")
    mixer.interface.new_socket(socket_type="NodeSocketColor", name="Denoised Image", in_out="OUTPUT")
    mixer.interface.new_socket(socket_type="NodeSocketColor", name="Noisy Image", in_out="OUTPUT")

    input_node.location = (-750, -110)
    output_node.location = (1455, -930)

    x = -330
    y = 250
    y_step = -170
    add_x_offset = 190
    last_output = None

    for i in range(MAX_LIGHTGROUPS):
        input_index_offset = MIXER_SOCKET_INDEX_START + i * MIXER_SOCKET_INDEX_STEP
        # Light Group i
        mixer.interface.new_socket(socket_type="NodeSocketColor", name=f"Light Group {i + 1}", in_out="INPUT")
        light_group_input = input_node.outputs[input_index_offset]
        # Gain
        gain = mixer.interface.new_socket(socket_type="NodeSocketFloat", name="Gain", in_out="INPUT")
        gain.default_value = 1
        gain.min_value = 0
        # Color
        color = mixer.interface.new_socket(socket_type="NodeSocketColor", name="Color", in_out="INPUT")
        color.default_value = (1, 1, 1, 1)

        editor_instance = mixer.nodes.new("CompositorNodeGroup")
        editor_instance.node_tree = editor

        mixer.links.new(light_group_input, editor_instance.inputs["Light Group"])
        mixer.links.new(input_node.outputs[input_index_offset + 1], editor_instance.inputs["Gain"])
        mixer.links.new(input_node.outputs[input_index_offset + 2], editor_instance.inputs["Color"])

        editor_instance.location = (x, y + i * y_step)

        if not last_output:
            # First time
            last_output = editor_instance.outputs[0]
        else:
            # Create add node
            add = mixer.nodes.new("CompositorNodeMixRGB")
            add.blend_type = "ADD"
            add.location = (editor_instance.location.x + i * add_x_offset, editor_instance.location.y)
            mixer.links.new(last_output, add.inputs[1])
            mixer.links.new(editor_instance.outputs[0], add.inputs[2])
            last_output = add.outputs[0]

    # Denoise node
    denoise_node = mixer.nodes.new("CompositorNodeDenoise")
    denoise_node.location = (1210, -845)
    mixer.links.new(last_output, denoise_node.inputs["Image"])
    mixer.links.new(input_node.outputs["ALBEDO"], denoise_node.inputs["Albedo"])
    mixer.links.new(input_node.outputs["AVG_SHADING_NORMAL"], denoise_node.inputs["Normal"])

    mixer.links.new(denoise_node.outputs[0], output_node.inputs["Denoised Image"])
    mixer.links.new(last_output, output_node.inputs["Noisy Image"])
    return mixer


def has_light_group_outputs(renderlayer_node):
    for output in renderlayer_node.outputs:
        if is_lightgroup_pass_name(output.name):
            return True
    return False


class LUXCORE_OT_create_lightgroup_nodes(bpy.types.Operator):
    bl_idname = "luxcore.create_lightgroup_nodes"
    bl_label = "Create/Update Light Group Nodes"
    bl_description = ("Creates a node group in the compositor which can be used to edit the scene "
                      "lighting after the render is complete. If one or more mixer nodes already "
                      "exist, this button can be used to update them after adding or removing "
                      "light groups")
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.scene.luxcore.lightgroups.custom) > 0

    def execute(self, context):
        scene = context.scene

        scene.use_nodes = True

        # Ensure that our node trees exist. If they already do, nothing happens in these methods
        # Group to edit one light group
        editor_tree = create_editor()
        # Group to mix multiple light groups
        mixer_tree = create_mixer(editor_tree)

        # Check if the nodes we need already exist
        mixer_nodes = []
        renderlayer_node = None

        for node in scene.node_tree.nodes:
            if node.bl_idname == "CompositorNodeRLayers":
                renderlayer_node = node
                continue

            if LUX_MIXER_INSTANCE_MARK in node:
                # Ensure that we have a working mixer instance that hasn't been repurposed to something else by the user
                if node.bl_idname == "CompositorNodeGroup" and node.node_tree == mixer_tree:
                    mixer_nodes.append(node)
                else:
                    # Node has been repurposed, remove our mark
                    del node[LUX_MIXER_INSTANCE_MARK]

        if not renderlayer_node:
            self.report({"ERROR"}, "Create a render layer node first.")
            return {"CANCELLED"}

        # Enable denoiser AOVs (needs to be done before refreshing the render layer node)
        view_layer = scene.view_layers[renderlayer_node.layer]
        view_layer.luxcore.aovs.avg_shading_normal = True
        view_layer.luxcore.aovs.albedo = True

        # Refresh render layer node to make sure its output names are synced to the light group names
        renderlayer_node.layer = renderlayer_node.layer

        # Nothing to do without lightgroup outputs
        if not has_light_group_outputs(renderlayer_node):
            self.report({"ERROR"}, "Create at least one custom light group, then press this button again.")
            return {"CANCELLED"}

        if len(mixer_nodes) == 0:
            #  Move render layer node to the left to make space for our setup
            renderlayer_node.location.x -= 500

            mixer_node = scene.node_tree.nodes.new("CompositorNodeGroup")
            mixer_node.node_tree = mixer_tree
            mixer_node.show_options = False  # Hides the node group dropdown
            mixer_node.label = "Light Group Mixer"
            mixer_node.width = 200
            mixer_node.location = (renderlayer_node.location.x + renderlayer_node.width + 100,
                                   renderlayer_node.location.y - 50)
            mixer_node[LUX_MIXER_INSTANCE_MARK] = True

            mixer_nodes.append(mixer_node)

        for mixer_node in mixer_nodes:
            # Connect render layer outputs to mixer inputs and make sure the names match
            scene.node_tree.links.new(renderlayer_node.outputs["ALBEDO"], mixer_node.inputs["ALBEDO"])
            scene.node_tree.links.new(renderlayer_node.outputs["AVG_SHADING_NORMAL"], mixer_node.inputs["AVG_SHADING_NORMAL"])
            lg_index = 0
            for output in renderlayer_node.outputs:
                # Blender does not remove old sockets on the render layer node, they are just disabled
                if output.enabled and is_lightgroup_pass_name(output.name):
                    mixer_input = mixer_node.inputs[MIXER_SOCKET_INDEX_START + lg_index * MIXER_SOCKET_INDEX_STEP]
                    scene.node_tree.links.new(output, mixer_input)
                    mixer_input.name = output.name
                    lg_index += 1

            # Disable inputs of unused light groups
            for i in range(MAX_LIGHTGROUPS):
                enabled = i <= len(scene.luxcore.lightgroups.custom)
                for j in range(MIXER_SOCKET_INDEX_STEP):
                    mixer_node.inputs[MIXER_SOCKET_INDEX_START + i * MIXER_SOCKET_INDEX_STEP + j].enabled = enabled

            renderlayer_node_image_output = renderlayer_node.outputs["Image"]
            if renderlayer_node_image_output.is_linked:
                scene.node_tree.links.new(mixer_node.outputs[0], renderlayer_node_image_output.links[0].to_socket)

        return {"FINISHED"}
