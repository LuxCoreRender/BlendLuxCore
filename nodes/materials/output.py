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

    interior_volume = PointerProperty(name="Interior Volume", type=bpy.types.NodeTree)
    exterior_volume = PointerProperty(name="Exterior Volume", type=bpy.types.NodeTree)

    def init(self, context):
        self.inputs.new("LuxCoreSocketMaterial", "Material")
        super().init(context)

    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)

        # TODO maybe there's a way to restrict the dropdowns to volume node trees?

        # Interior volume

        layout.label("Interior Volume Nodes:")
        row = layout.row(align=True)
        row.template_ID(self, "interior_volume")

        # Operator for new node tree
        interior_volume = self.interior_volume
        new_text = "" if interior_volume else "New"
        new = row.operator("luxcore.vol_nodetree_new", text=new_text, icon="ZOOMIN")
        new.target = "interior_volume"

        # Warning if not the right node tree type
        if interior_volume and interior_volume.bl_idname != "luxcore_volume_nodes":
            layout.label("Not a volume node tree!", icon="ERROR")

        # Exterior volume

        layout.label("Exterior Volume Nodes:")
        row = layout.row(align=True)
        row.template_ID(self, "exterior_volume")

        # Operator for new node tree
        exterior_volume = self.exterior_volume
        new_text = "" if exterior_volume else "New"
        new = row.operator("luxcore.vol_nodetree_new", text=new_text, icon="ZOOMIN")
        new.target = "exterior_volume"

        # Warning if not the right node tree type
        if exterior_volume and exterior_volume.bl_idname != "luxcore_volume_nodes":
            layout.label("Not a volume node tree!", icon="ERROR")

    def export(self, props, luxcore_name):
        # We have to export volumes before the material definition because LuxCore properties
        # do not support forward declarations (the volume has to be already defined when it is
        # referenced in the material)
        # TODO: default exterior/interior volume
        # TODO: cache volume export (can be slow in case of smoke. But maybe a smoke cache is enough or even better?)
        prefix = "scene.materials." + luxcore_name + "."
        self._convert_volume(self.interior_volume, props, prefix + "volume.interior")
        self._convert_volume(self.exterior_volume, props, prefix + "volume.exterior")

        self.inputs["Material"].export(props, luxcore_name)

    def _convert_volume(self, node_tree, props, property_str):
        """
        property_str should be of the form
        "scene.materials.<luxcore_name>.volume.<interior/exterior>"
        """
        if node_tree is None:
            return

        try:
            active_output = get_active_output(node_tree, "LuxCoreNodeVolOutput")
            luxcore_name = utils.get_unique_luxcore_name(node_tree)
            active_output.export(props, luxcore_name)

            props.Set(pyluxcore.Property(property_str, luxcore_name))
        except Exception as error:
            # TODO: collect exporter errors
            print("ERROR in volume", node_tree.name)
            print(error)