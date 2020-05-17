import webbrowser
import bpy
from bpy.props import StringProperty, BoolProperty
from .utils import init_vol_node_tree, poll_node
from ..utils.errorlog import LuxCoreErrorLog


def _use_cycles_material_nodes():
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.node_tree:
            mat.luxcore.use_cycles_nodes = True


class LUXCORE_OT_use_cycles_settings(bpy.types.Operator):
    bl_idname = "luxcore.use_cycles_settings"
    bl_label = "Use Cycles Settings"
    bl_description = "Use Cycles material nodes, light settings, world settings etc. wherever possible"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        _use_cycles_material_nodes()

        for light in bpy.data.lights:
            light.luxcore.use_cycles_settings = True
            light.update_tag()

        for world in bpy.data.worlds:
            world.luxcore.use_cycles_settings = True
            world.update_tag()

        return {"FINISHED"}


class LUXCORE_OT_use_cycles_nodes_everywhere(bpy.types.Operator):
    bl_idname = "luxcore.use_cycles_nodes_everywhere"
    bl_label = "Use Cycles nodes on all materials"
    bl_description = 'Enable the "Use Cycles nodes" checkbox on all materials that have a Cycles nodetree'
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        _use_cycles_material_nodes()
        return {"FINISHED"}


class LUXCORE_OT_errorlog_clear(bpy.types.Operator):
    bl_idname = "luxcore.errorlog_clear"
    bl_label = "Clear Error Log"
    bl_description = "(Log is automatically cleared when a final or viewport render is started)"

    def execute(self, context):
        LuxCoreErrorLog.clear()
        return {"FINISHED"}


class LUXCORE_OT_switch_texture_context(bpy.types.Operator):
    bl_idname = "luxcore.switch_texture_context"
    bl_label = ""
    bl_description = "Switch the texture context"

    target: bpy.props.StringProperty()

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

    target: bpy.props.StringProperty()

    def execute(self, context):
        assert self.target in {"SCENE", "RENDER", "VIEW_LAYER", "WORLD", "OBJECT", "CONSTRAINT",
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
    bl_label = "Update device list"
    bl_description = "Use this button if the device list below does not match your computer's devices"

    def execute(self, context):
        devices = context.scene.luxcore.devices
        devices.init_devices(devices.get_device_props())
        return {"FINISHED"}


class LUXCORE_OT_add_node(bpy.types.Operator):
    bl_idname = "luxcore.add_node"
    bl_label = "Add"

    node_type: StringProperty()
    socket_type: StringProperty()
    input_socket: StringProperty()

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
        world = context.scene.world
        world.luxcore.sun = context.object
        world.update_tag()
        return {"FINISHED"}


class LUXCORE_OT_copy_error_to_clipboard(bpy.types.Operator):
    bl_idname = "luxcore.copy_error_to_clipboard"
    bl_label = ""
    bl_description = "Copy the error message to clipboard so you can paste it with Ctrl+V"

    message: StringProperty()

    def execute(self, context):
        context.window_manager.clipboard = self.message
        return {"FINISHED"}


class LUXCORE_OT_open_website(bpy.types.Operator):
    bl_idname = "luxcore.open_website"
    bl_label = ""
    bl_description = "Open related website in the web browser"
    # Note: use the "URL" icon and a custom text when using this operator:
    # op = layout.operator("luxcore.open_website", text="Wiki Page", icon=icons.URL)
    # op.url = "https://www.example.com"

    url: StringProperty()

    def execute(self, context):
        webbrowser.open(self.url)
        return {"FINISHED"}


class LUXCORE_OT_open_website_popup(bpy.types.Operator):
    bl_idname = "luxcore.open_website_popup"
    bl_label = "Open Website"
    bl_description = "Open related website in the web browser"
    # This operator is intended to be used as a popup with short message and OK button.
    # When the user clicks the OK button, the url is opened.
    # Usage:
    # bpy.ops.luxcore.open_website_popup("INVOKE_DEFAULT",
    #                                    message="Short message",
    #                                    url="http://example.com/")

    message: StringProperty()
    url: StringProperty()

    def draw(self, context):
        layout = self.layout
        if self.message:
            layout.label(text=self.message)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        webbrowser.open(self.url)
        return {"FINISHED"}


class LUXCORE_OT_select_object(bpy.types.Operator):
    bl_idname = "luxcore.select_object"
    bl_label = "Select Object"
    bl_description = "Select this object"
    bl_options = {"UNDO"}

    obj_name: StringProperty()

    def execute(self, context):
        if self.obj_name not in context.scene.objects:
            self.report({"ERROR"}, "Object was deleted or renamed")
            return {"CANCELLED"}
        if context.active_object and context.active_object.mode != "OBJECT":
            self.report({"ERROR"}, "Change to object mode first")
            return {"CANCELLED"}

        obj = context.scene.objects[self.obj_name]
        bpy.ops.object.select_all(action="DESELECT")
        if not obj.select_get():
            obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}
