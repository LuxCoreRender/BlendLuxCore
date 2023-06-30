from bl_ui.properties_material import MaterialButtonsPanel, MATERIAL_PT_viewport
from bpy.types import Panel, Menu
from ..operators.node_tree_presets import LUXCORE_OT_preset_material
from .. import icons
from ..ui.icons import icon_manager
original_viewport_draw = None


def lux_mat_template_ID(layout, material):
    row = layout.row(align=True)
    row.operator("luxcore.material_select", text="", icon_value=icon_manager.get_icon_id("add"))

    if material:
        row.prop(material, "name", text="", icon_value=icon_manager.get_icon_id("logotype"))
        if material.users > 1:
            # TODO this thing is too wide
            row.operator("luxcore.material_copy", text=str(material.users), icon_value=icon_manager.get_icon_id("logotype"))
        row.prop(material, "use_fake_user", text="", icon_value=icon_manager.get_icon_id("fake"))
        row.operator("luxcore.material_copy", text="", icon_value=icon_manager.get_icon_id("copy"))
        row.operator("luxcore.material_unlink", text="", icon_value=icon_manager.get_icon_id("unlink"))
    else:
        row.operator("luxcore.material_new", text="New", icon_value=icon_manager.get_icon_id("logotype"))
    return row


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

        if obj:
            # Note that we don't use layout.template_ID() because we can't
            # control the copy operator in that template.
            # So we mimic our own template_ID.
            row = lux_mat_template_ID(layout, obj.active_material)

            if slot:
                row = row.row()
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif mat:
            layout.template_ID(space, "pin_id")
            layout.separator()

        if mat:
            if mat.luxcore.node_tree or (mat.use_nodes and mat.node_tree and mat.luxcore.use_cycles_nodes):
                layout.operator("luxcore.material_show_nodetree", icon_value=icon_manager.get_icon_id("nodes"))

            if not mat.luxcore.node_tree and not mat.luxcore.use_cycles_nodes:
                layout.operator("luxcore.mat_nodetree_new", icon_value=icon_manager.get_icon_id("nodes"), text="Use LuxCore Material Nodes")

            if mat.use_nodes and mat.node_tree:
                layout.prop(mat.luxcore, "use_cycles_nodes")


class LUXCORE_PT_material_presets(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Node Tree Presets"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        if context.material and context.material.luxcore.use_cycles_nodes:
            return False
        return engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout

        row = layout.row()

        for category, presets in LUXCORE_OT_preset_material.categories.items():
            col = row.column()
            col.label(text=category)

            for preset in presets:
                op = col.operator("luxcore.preset_material", text=preset)
                op.preset = preset
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

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
        
        
class LUXCORE_PT_material_settings(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Settings"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 4

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.material and (engine == "LUXCORE") and context.material.luxcore.use_cycles_nodes

    def draw(self, context):
        layout = self.layout
        layout.prop(context.material, "pass_index")

def lux_viewport_draw(self, context):
    layout = self.layout

    mat = context.material

    if context.scene.render.engine == "LUXCORE":
        if mat.luxcore.auto_vp_color:
            split = layout.split(factor=0.8)
            split.prop(mat.luxcore, "auto_vp_color")
            row = split.row()
            row.enabled = not mat.luxcore.auto_vp_color
            row.prop(mat, "diffuse_color", text="")
        else:
            layout.prop(mat.luxcore, "auto_vp_color")
            layout.prop(mat, "diffuse_color", text="Viewport Color")
    else:
        layout.use_property_split = True
        col = layout.column()
        col.prop(mat, "diffuse_color", text="Color")
        col.prop(mat, "metallic")
        col.prop(mat, "roughness")


def register():
    global original_viewport_draw
    original_viewport_draw = MATERIAL_PT_viewport.draw
    MATERIAL_PT_viewport.draw = lux_viewport_draw


def unregister():
    MATERIAL_PT_viewport.draw = original_viewport_draw
