import bpy
from ...bin import pyluxcore
from ... import utils
from bpy.props import BoolProperty, PointerProperty
from ..output import LuxCoreNodeOutput, update_active, get_active_output


class LuxCoreNodeMatOutput(LuxCoreNodeOutput):
    """
    Material output node.
    This is where the export starts (if the output is active).
    """
    bl_label = "Material Output"
    bl_width_min = 160

    active = BoolProperty(name="Active", default=True, update=update_active)

    # TODO: option to sync volume settings among output nodes (workflow improvement)
    interior_volume = PointerProperty(name="Interior Volume", type=bpy.types.NodeTree)
    exterior_volume = PointerProperty(name="Exterior Volume", type=bpy.types.NodeTree)

    def init(self, context):
        self.inputs.new("LuxCoreSocketMaterial", "Material")
        super().init(context)

    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)

        # TODO maybe there's a way to restrict the dropdowns to volume node trees?

        layout.label("Interior Volume Nodes:")
        self._draw_volume_controls(context, layout, "interior_volume")

        layout.label("Exterior Volume Nodes:")
        self._draw_volume_controls(context, layout, "exterior_volume")

    def _draw_volume_controls(self, context, layout, volume_str):
        """ volume_str can be either "interior_volume" or "exterior_volume" """
        assert hasattr(self, volume_str)
        volume = getattr(self, volume_str)

        row = layout.row(align=True)
        # We have to disable the new operator if node tree is linked from a library
        # Because if it is enabled, the user can create and link a node tree that will not be saved
        row.enabled = self.id_data.library is None
        row.template_ID(self, volume_str)

        # Operator for new node tree
        new_text = "" if volume else "New"
        new = row.operator("luxcore.vol_nodetree_new", text=new_text, icon="ZOOMIN")
        # We have to tell the operator where the new node tree should be linked to
        new.target = volume_str

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
            bpy.context.luxcore.errorlog.add_warning(msg)

    
    def _convert_fallback(self, props, luxcore_name):
        prefix = "scene.materials." + luxcore_name + "."
        props.Set(pyluxcore.Property(prefix + "type", "matte"))
        props.Set(pyluxcore.Property(prefix + "kd", [0, 0, 0]))
