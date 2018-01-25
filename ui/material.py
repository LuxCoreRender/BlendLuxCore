from bl_ui.properties_material import MaterialButtonsPanel
from bpy.types import Panel, Menu
from .. import utils


class LUXCORE_PT_context_material(MaterialButtonsPanel, Panel):
    """
    Material UI Panel
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return (context.material or context.object) and (engine == "LUXCORE")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        obj = context.object
        slot = context.material_slot
        space = context.space_data

        # Re-create the Blender material UI, but without the surface/wire/volume/halo buttons
        if obj:
            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", obj, "material_slots", obj, "active_material_index", rows=2)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon="ZOOMIN", text="")
            col.operator("object.material_slot_remove", icon="ZOOMOUT", text="")

            col.menu("MATERIAL_MT_specials", icon="DOWNARROW_HLT", text="")

            if obj.mode == "EDIT":
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        split = layout.split(percentage=0.68)

        if obj:
            row = split.row(align=True)
            row.prop(obj, "active_material", text="")
            if obj.active_material:
                row.operator("luxcore.material_copy", text="", icon="COPY_ID")
                text_new = ""
            else:
                text_new = "New"

            row.operator("luxcore.material_new", text=text_new, icon="ZOOMIN")

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
            if mat.luxcore.node_tree:
                tree_name = utils.get_tree_name_with_lib(mat.luxcore.node_tree)
                layout.label('Material Node Tree: "%s"' % tree_name, icon="NODETREE")
            else:
                layout.operator("luxcore.mat_nodetree_new", icon="ZOOMIN", text="Use Material Nodes")

            # Warning if not the right node tree type
            # TODO: should now never be possible - remove this?
            if mat.luxcore.node_tree and mat.luxcore.node_tree.bl_idname != "luxcore_material_nodes":
                layout.label("Not a material node tree!", icon="ERROR")

        layout.separator()
        layout.menu("LUXCORE_MT_node_tree_preset")
