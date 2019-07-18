from bl_ui.properties_material import MaterialButtonsPanel
from bpy.types import Panel, Menu
from .. import utils
from ..operators.node_tree_presets import LUXCORE_OT_preset_material
from ..ui import icons


class LUXCORE_PT_context_material(MaterialButtonsPanel, Panel):
    """
    Material UI Panel
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = ""
    bl_options = {"HIDE_HEADER"}
    bl_order = 1

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
            is_sortable = len(obj.material_slots) > 1
            rows = 1
            if (is_sortable):
                rows = 4

            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", obj, "material_slots", obj, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ADD', text="")
            col.operator("object.material_slot_remove", icon='REMOVE', text="")

            col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

            if obj.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        split = layout.split(factor=0.65)

        if obj:
            # TODO 2.8 recreate our own version of this template with our custom new/copy operators
            split.template_ID(obj, "active_material", new="material.new")
            row = split.row()

            if slot:
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif mat:
            split.template_ID(space, "pin_id")
            split.separator()

        if mat:
            if mat.luxcore.node_tree:
                row = layout.row()
                split = row.split(factor=0.25)
                split.label(text=utils.pluralize("%d User", mat.users))
                if not mat.luxcore.use_cycles_nodes:
                    tree_name = utils.get_name_with_lib(mat.luxcore.node_tree)
                    split.label(text='Nodes: "%s"' % tree_name, icon="NODETREE")
                    split.operator("luxcore.material_show_nodetree", icon=icons.SHOW_NODETREE)

            if mat.use_nodes and mat.node_tree:
                layout.prop(mat.luxcore, "use_cycles_nodes")
                # TODO show_nodetree operator for Cycles node tree

            if not mat.luxcore.node_tree and not mat.luxcore.use_cycles_nodes:
                layout.operator("luxcore.mat_nodetree_new", icon="NODETREE", text="Use LuxCore Material Nodes")


class LUXCORE_PT_material_presets(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Node Tree Presets"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine == "LUXCORE" and (context.material and not context.material.luxcore.use_cycles_nodes)

    def draw(self, context):
        layout = self.layout

        row = layout.row()

        for category, presets in LUXCORE_OT_preset_material.categories.items():
            col = row.column()
            col.label(text=category)

            for preset in presets:
                op = col.operator("luxcore.preset_material", text=preset)
                op.preset = preset


##class LUXCORE_PT_settings(MaterialButtonsPanel, Panel):
##    bl_label = "Settings"
##    bl_context = "material"
##    bl_options = {'DEFAULT_CLOSED'}
##
##    @classmethod
##    def poll(cls, context):
##        engine = context.scene.render.engine
##        return context.material and engine == "LUXCORE"
##
##    def draw(self, context):
##        layout = self.layout
##        mat = context.material
##
##        if mat.luxcore.auto_vp_color:
##            split = layout.split(factor=0.8)
##            split.prop(mat.luxcore, "auto_vp_color")
##            row = split.row()
##            row.enabled = not mat.luxcore.auto_vp_color
##            row.prop(mat, "diffuse_color", text="")
##        else:
##            layout.prop(mat.luxcore, "auto_vp_color")
##            layout.prop(mat, "diffuse_color", text="Viewport Color")


class LUXCORE_PT_material_preview(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Preview"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 3

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.material and (engine == "LUXCORE")

    def draw(self, context):
        layout = self.layout
        layout.template_preview(context.material)
        row = layout.row(align=True)
        preview = context.material.luxcore.preview
        row.prop(preview, "zoom")
        row.prop(preview, "size")
