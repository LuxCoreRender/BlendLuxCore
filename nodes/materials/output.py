import bpy
from ...bin import pyluxcore
from ... import utils
from ...utils import ui as utils_ui
from ...utils import node as utils_node
from bpy.props import BoolProperty, PointerProperty
from ..output import LuxCoreNodeOutput, update_active, get_active_output
from ...ui import ICON_VOLUME

SHADOWCATCHER_DESC = (
    "Make this material transparent and only catch shadows on it. "
    "Used for compositing 3D objects into real-world footage. "
    "Remember to enable transparent film in camera settings"
)


class LuxCoreNodeMatOutput(LuxCoreNodeOutput):
    """
    Material output node.
    This is where the export starts (if the output is active).
    """
    bl_label = "Material Output"
    bl_width_min = 220

    active = BoolProperty(name="Active", default=True, update=update_active)
    is_shadow_catcher = BoolProperty(name="Shadow Catcher", default=False,
                                     description=SHADOWCATCHER_DESC)

    def init(self, context):
        self.inputs.new("LuxCoreSocketMaterial", "Material")
        # TODO: option to sync volume settings among output nodes (workflow improvement)
        self.inputs.new("LuxCoreSocketVolume", "Interior Volume")
        self.inputs.new("LuxCoreSocketVolume", "Exterior Volume")
        super().init(context)

    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)

        # Shadow catcher
        engine_is_bidir = context.scene.luxcore.config.engine == "BIDIR"
        col = layout.column()
        col.active = not engine_is_bidir
        col.prop(self, "is_shadow_catcher")

        if engine_is_bidir:
            col.label("Not supported by Bidir engine", icon="INFO")
        elif self.is_shadow_catcher and context.scene.camera:
            pipeline = context.scene.camera.data.luxcore.imagepipeline
            if not pipeline.transparent_film:
                layout.label("Needs transparent film:")
                layout.prop(pipeline, "transparent_film", text="Enable Transparent Film",
                            icon="CAMERA_DATA", emboss=True)

        # TODO Remove this in the future
        if "Interior Volume" not in self.inputs:
            layout.label("Outdated ouput, replace it!", icon="ERROR")


    def export(self, props, luxcore_name):
        prefix = "scene.materials." + luxcore_name + "."

        # We have to export volumes before the material definition because LuxCore properties
        # do not support forward declarations (the volume has to be already defined when it is
        # referenced in the material)

        interior_volume_name = None
        exterior_volume_name = None

        interior_pointer = utils_node.get_linked_node(self.inputs["Interior Volume"])
        if interior_pointer:
            node_tree = interior_pointer.node_tree
            interior_volume_name = self._convert_volume(node_tree, props)

        exterior_pointer = utils_node.get_linked_node(self.inputs["Exterior Volume"])
        if exterior_pointer:
            node_tree = exterior_pointer.node_tree
            exterior_volume_name = self._convert_volume(node_tree, props)

        # Export the material
        exported_name = self.inputs["Material"].export(props, luxcore_name)

        # Attach the volumes
        if interior_volume_name:
            props.Set(pyluxcore.Property(prefix + "volume.interior", interior_volume_name))
        if exterior_volume_name:
            props.Set(pyluxcore.Property(prefix + "volume.exterior", exterior_volume_name))

        if exported_name is None or exported_name != luxcore_name:
            # Export failed, e.g. because no node is linked or it's not a material node
            # Define a black material that signals an unconnected material socket
            self._convert_fallback(props, luxcore_name)

        props.Set(pyluxcore.Property(prefix + "shadowcatcher.enable", self.is_shadow_catcher))

    def _convert_volume(self, node_tree, props):
        if node_tree is None:
            return None

        try:
            luxcore_name = utils.get_luxcore_name(node_tree)
            active_output = get_active_output(node_tree)
            active_output.export(props, luxcore_name)
            return luxcore_name
        except Exception as error:
            msg = 'Node Tree "%s": %s' % (node_tree.name, error)
            bpy.context.scene.luxcore.errorlog.add_warning(msg)
            return None

    
    def _convert_fallback(self, props, luxcore_name):
        prefix = "scene.materials." + luxcore_name + "."
        props.Set(pyluxcore.Property(prefix + "type", "matte"))
        props.Set(pyluxcore.Property(prefix + "kd", [0, 0, 0]))
