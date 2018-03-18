import bpy
from bpy.props import StringProperty, BoolProperty

# Ensure initialization (note: no need to initialize utils)
from . import (
    camera, material, node_tree_presets, pointer_node, texture, world, ior_presets
)
from .utils import init_vol_node_tree, poll_node


class LUXCORE_OT_errorlog_clear(bpy.types.Operator):
    bl_idname = "luxcore.errorlog_clear"
    bl_label = "Clear Error Log"
    bl_description = "(Log is automatically cleared when a final or viewport render is started)"

    def execute(self, context):
        context.scene.luxcore.errorlog.clear()
        return {"FINISHED"}


class LUXCORE_OT_switch_texture_context(bpy.types.Operator):
    bl_idname = "luxcore.switch_texture_context"
    bl_label = ""
    bl_description = "Switch the texture context"

    target = bpy.props.StringProperty()

    def execute(self, context):
        assert self.target in {"PARTICLES", "OTHER"}

        space = context.space_data
        try:
            space.texture_context = self.target
        except TypeError:
            # Sometimes one of the target contexts is not available
            pass

        return {"FINISHED"}


class LUXCORE_OT_switch_space_data_context(bpy.types.Operator):
    bl_idname = "luxcore.switch_space_data_context"
    bl_label = ""
    bl_description = "Switch the properties context (Render, Scene, Material, Texture, ...)"

    target = bpy.props.StringProperty()

    def execute(self, context):
        assert self.target in {"SCENE", "RENDER", "RENDER_LAYER", "WORLD", "OBJECT", "CONSTRAINT",
                               "MODIFIER", "DATA", "BONE", "BONE_CONSTRAINT", "MATERIAL", "TEXTURE",
                               "PARTICLES", "PHYSICS"}

        space = context.space_data
        space.context = self.target

        return {"FINISHED"}


class LUXCORE_OT_switch_to_camera_settings(bpy.types.Operator):
    """
    Used in render layer UI
    """
    bl_idname = "luxcore.switch_to_camera_settings"
    bl_label = "Switch to camera settings to solve"
    bl_description = "Solve this issue by using a non-automatic tonemapper in the imagepipeline settings"

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def execute(self, context):
        context.scene.objects.active = context.scene.camera
        bpy.ops.luxcore.switch_space_data_context(target="DATA")
        return {"FINISHED"}


class LUXCORE_OT_set_suggested_clamping_value(bpy.types.Operator):
    bl_idname = "luxcore.set_suggested_clamping_value"
    bl_label = ""
    bl_description = (
        "Apply the suggested clamping value. Note that this is only a starting point, "
        "you might need to adjust the value to get the best results for your scene"
    )

    def execute(self, context):
        config = context.scene.luxcore.config
        config.path.use_clamping = True
        config.path.clamping = config.path.suggested_clamping_value

        return {"FINISHED"}


class LUXCORE_OT_update_opencl_devices(bpy.types.Operator):
    bl_idname = "luxcore.update_opencl_devices"
    bl_label = "Update OpenCL device list"

    def execute(self, context):
        opencl = context.scene.luxcore.opencl
        device_list = opencl.get_opencl_devices()
        opencl.init_devices(device_list)
        return {"FINISHED"}


class LUXCORE_OT_add_node(bpy.types.Operator):
    bl_idname = "luxcore.add_node"
    bl_label = "Add"

    node_type = StringProperty()
    socket_type = StringProperty()
    input_socket = StringProperty()

    @classmethod
    def poll(cls, context):
        return poll_node(context)

    def execute(self, context):
        node = context.node
        node_tree = node.id_data
        new_node = node_tree.nodes.new(self.node_type)
        # Place new node a bit to the left and down
        offset_x = new_node.width + 50
        new_node.location = (node.location.x - offset_x, node.location.y - 100)

        # Link
        output = 0
        for out in new_node.outputs:
            if out.bl_idname == self.socket_type:
                output = out.name
                break

        node_tree.links.new(new_node.outputs[output], node.inputs[self.input_socket])

        # Special stuff only needed by material output
        if self.socket_type == "LuxCoreSocketVolume" and self.node_type == "LuxCoreNodeTreePointer":
            name = "Volume"

            vol_tree = bpy.data.node_groups.new(name=name, type="luxcore_volume_nodes")
            init_vol_node_tree(vol_tree)

            new_node.node_tree = vol_tree

        return {"FINISHED"}


class LUXCORE_OT_attach_sun_to_sky(bpy.types.Operator):
    bl_idname = "luxcore.attach_sun_to_sky"
    bl_label = "Attach to Sky"
    bl_description = "Attach if the sky should use the rotation and turbidity settings of this sun"

    @classmethod
    def poll(cls, context):
        return context.scene.world and context.object

    def execute(self, context):
        context.scene.world.luxcore.sun = context.object
        return {"FINISHED"}
