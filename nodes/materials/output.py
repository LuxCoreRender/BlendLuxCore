import bpy
from ...bin import pyluxcore
from ... import utils
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

    # TODO: option to sync volume settings among output nodes (workflow improvement)
    interior_volume = PointerProperty(name="Interior Volume", type=bpy.types.NodeTree)
    exterior_volume = PointerProperty(name="Exterior Volume", type=bpy.types.NodeTree)
    is_shadow_catcher = BoolProperty(name="Shadow Catcher", default=False,
                                     description=SHADOWCATCHER_DESC)

    def init(self, context):
        self.inputs.new("LuxCoreSocketMaterial", "Material")
        super().init(context)

    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)

        layout.label("Interior Volume Nodes:")
        self._draw_volume_controls(context, layout, "interior_volume")

        layout.label("Exterior Volume Nodes:")
        self._draw_volume_controls(context, layout, "exterior_volume")

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

    def _draw_volume_controls(self, context, layout, volume_str):
        """ volume_str can be either "interior_volume" or "exterior_volume" """
        assert hasattr(self, volume_str)
        volume = getattr(self, volume_str)

        split = layout.split(percentage=0.6, align=True)
        row = split.row(align=True)

        # Volume dropdown
        if volume:
            text = utils.get_tree_name_with_lib(volume)
        else:
            text = "-"

        if volume_str == "interior_volume":
            row.menu("LUXCORE_VOLUME_MT_node_tree_interior", icon=ICON_VOLUME, text=text)
        else:
            row.menu("LUXCORE_VOLUME_MT_node_tree_exterior", icon=ICON_VOLUME, text=text)

        row = split.row(align=True)

        # Operator to quickly switch to this volume node tree
        if volume:
            op = row.operator("luxcore.switch_to_node_tree")
            op.name = volume.name

        # Operator for new node tree
        new_text = "" if volume else "New"
        op = row.operator("luxcore.vol_nodetree_new", text=new_text, icon="ZOOMIN")
        # We have to tell the operator where the new node tree should be linked to
        op.target = volume_str

        # Operator to unlink node tree
        if volume:
            op = row.operator("luxcore.vol_nodetree_unlink", text="", icon="X")
            op.target = volume_str

        # Warning if not the right node tree type
        if volume and volume.bl_idname != "luxcore_volume_nodes":
            layout.label("Not a volume node tree!", icon="ERROR")

    def export(self, props, luxcore_name):
        # We have to export volumes before the material definition because LuxCore properties
        # do not support forward declarations (the volume has to be already defined when it is
        # referenced in the material)
        # TODO: default exterior/interior volume
        # TODO: cache volume export (can be slow in case of smoke. But maybe a smoke cache is enough or even better?)
        prefix = "scene.materials." + luxcore_name + "."

        exported_name = self.inputs["Material"].export(props, luxcore_name)
        if exported_name is None or exported_name != luxcore_name:
            # Export failed, e.g. because no node is linked or it's not a material node
            # Define a black material that signals an unconnected material socket
            self._convert_fallback(props, luxcore_name)

        self._convert_volume(self.interior_volume, props, prefix + "volume.interior")
        self._convert_volume(self.exterior_volume, props, prefix + "volume.exterior")

        props.Set(pyluxcore.Property(prefix + "shadowcatcher.enable", self.is_shadow_catcher))

    def _convert_volume(self, node_tree, props, property_str):
        """
        property_str should be of the form
        "scene.materials.<luxcore_name>.volume.<interior/exterior>"
        """
        if node_tree is None:
            return

        try:
            active_output = get_active_output(node_tree)
            luxcore_name = utils.get_luxcore_name(node_tree)
            active_output.export(props, luxcore_name)

            props.Set(pyluxcore.Property(property_str, luxcore_name))
        except Exception as error:
            msg = 'Node Tree "%s": %s' % (node_tree.name, error)
            bpy.context.scene.luxcore.errorlog.add_warning(msg)

    
    def _convert_fallback(self, props, luxcore_name):
        prefix = "scene.materials." + luxcore_name + "."
        props.Set(pyluxcore.Property(prefix + "type", "matte"))
        props.Set(pyluxcore.Property(prefix + "kd", [0, 0, 0]))
