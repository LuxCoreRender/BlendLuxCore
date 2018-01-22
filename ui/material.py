from bl_ui.properties_material import MaterialButtonsPanel
from bpy.types import Panel, Menu
from ..operators.node_tree import LUXCORE_OT_preset_material


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
            # We use our custom new material operator here
            split.template_ID(obj, "active_material", new="luxcore.material_new")

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
            layout.label("LuxCore Material Nodes:", icon="NODETREE")
            layout.template_ID(mat.luxcore, "node_tree", new="luxcore.mat_nodetree_new")

            # Warning if not the right node tree type
            if mat.luxcore.node_tree and mat.luxcore.node_tree.bl_idname != "luxcore_material_nodes":
                layout.label("Not a material node tree!", icon="ERROR")

            # layout.operator_menu_enum("object.select_by_type", "type", text="Select All by Type...")

        layout.separator()
        layout.menu("luxcore_menu_node_tree_preset")


class LUXCORE_MATERIAL_PT_node_tree_preset(Menu):
    bl_idname = "luxcore_menu_node_tree_preset"
    bl_label = "Add Node Tree Preset"
    bl_description = "Add a pre-definied node setup"

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        for category, presets in LUXCORE_OT_preset_material.categories.items():
            col = row.column()
            col.label(category)

            for preset in presets:
                op = col.operator("luxcore.preset_material", text=preset.title())
                op.preset = preset
