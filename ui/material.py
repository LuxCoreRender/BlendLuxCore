import bl_ui
import bpy
from . import ICON_VOLUME


class LuxCoreMaterialHeader(bl_ui.properties_material.MaterialButtonsPanel, bpy.types.Panel):
    """
    Material UI Panel
    """
    COMPAT_ENGINES = "LUXCORE"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return (context.material or context.object) and (engine == "LUXCORE")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data

        # Re-create the Blender material UI, but without the surface/wire/volume/halo buttons
        if ob:
            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=2)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon="ZOOMIN", text="")
            col.operator("object.material_slot_remove", icon="ZOOMOUT", text="")

            col.menu("MATERIAL_MT_specials", icon="DOWNARROW_HLT", text="")

            if ob.mode == "EDIT":
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        split = layout.split(percentage=0.68)

        if ob:
            # We use our custom new material operator here
            split.template_ID(ob, "active_material", new="luxcore.material_new")

            if slot:
                row = split.row()
                row.prop(slot, "link", text="")
            else:
                row = split.row()
                row.label()
        elif mat:
            split.template_ID(space, "pin_id")
            split.separator()

        if mat:
            # Material node tree
            layout.label("Material Nodes:")
            layout.template_ID(mat.luxcore, "node_tree", new="luxcore.mat_nodetree_new")

            # Warning if not the right node tree type
            if mat.luxcore.node_tree and mat.luxcore.node_tree.bl_idname != "luxcore_material_nodes":
                layout.label("Not a material node tree!", icon="ERROR")

            # TODO maybe there's a way to restrict the dropdowns to volume node trees?

            # Interior volume

            layout.label("Interior Volume Nodes:")
            row = layout.row(align=True)
            row.template_ID(mat.luxcore, "interior_volume")

            # Operator for new node tree
            interior_volume = mat.luxcore.interior_volume
            new_text = "" if interior_volume else "New"
            new = row.operator("luxcore.vol_nodetree_new", text=new_text, icon="ZOOMIN")
            new.target = "interior_volume"

            # Warning if not the right node tree type
            if interior_volume and interior_volume.bl_idname != "luxcore_volume_nodes":
                layout.label("Not a volume node tree!", icon="ERROR")

            # Exterior volume

            layout.label("Exterior Volume Nodes:")
            row = layout.row(align=True)
            row.template_ID(mat.luxcore, "exterior_volume")

            # Operator for new node tree
            exterior_volume = mat.luxcore.exterior_volume
            new_text = "" if exterior_volume else "New"
            new = row.operator("luxcore.vol_nodetree_new", text=new_text, icon="ZOOMIN")
            new.target = "exterior_volume"

            # Warning if not the right node tree type
            if exterior_volume and exterior_volume.bl_idname != "luxcore_volume_nodes":
                layout.label("Not a volume node tree!", icon="ERROR")
