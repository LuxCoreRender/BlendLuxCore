import bpy

# Ensure initialization (note: no need to initialize utils)
from . import (
    camera, material, node_tree_presets, pointer_node, texture, world
)


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


class LUXCORE_OT_set_optimal_clamping_value(bpy.types.Operator):
    bl_idname = "luxcore.set_optimal_clamping_value"
    bl_label = ""
    bl_description = "Apply the optimal clamping value"

    def execute(self, context):
        config = context.scene.luxcore.config
        config.path.use_clamping = True
        config.path.clamping = config.path.optimal_clamping_value

        return {"FINISHED"}


class LUXCORE_OT_update_opencl_devices(bpy.types.Operator):
    bl_idname = "luxcore.update_opencl_devices"
    bl_label = "Update OpenCL device list"

    def execute(self, context):
        opencl = context.scene.luxcore.opencl
        device_list = opencl.get_opencl_devices()
        opencl.init_devices(device_list)
        return {"FINISHED"}
