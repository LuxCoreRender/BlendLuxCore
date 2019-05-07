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
            col.operator("object.material_slot_add", icon=icons.ADD, text="")
            col.operator("object.material_slot_remove", icon=icons.REMOVE, text="")

            col.menu("MATERIAL_MT_specials", icon="DOWNARROW_HLT", text="")

            if obj.mode == "EDIT":
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        split = layout.split(percentage=0.68)

        if obj:
            # Note that we don't use layout.template_ID() because we can't
            # control the copy operator in that template.
            # So we mimic our own template_ID.
            row = split.row(align=True)
            sub = row.split(align=True, percentage=1 / (context.region.width * 0.015))
            sub.operator("luxcore.material_select", icon=icons.MATERIAL, text="")
            row = sub.row(align=True)
            if obj.active_material:
                row.prop(obj.active_material, "name", text="")
                row.prop(obj.active_material, "use_fake_user", text="", toggle=True, icon="FONT_DATA")  # :^)
                row.operator("luxcore.material_copy", text="", icon="COPY_ID")
                text_new = ""
            else:
                text_new = "New"

            row.operator("luxcore.material_new", text=text_new, icon=icons.ADD)

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
                row = layout.row()
                split = row.split(percentage=0.25)
                split.label(utils.pluralize("%d User", mat.users))
                tree_name = utils.get_name_with_lib(mat.luxcore.node_tree)
                split.label('Nodes: "%s"' % tree_name, icon="NODETREE")
                split.operator("luxcore.material_show_nodetree", icon=icons.SHOW_NODETREE)
            else:
                layout.operator("luxcore.mat_nodetree_new", icon="NODETREE", text="Use Material Nodes")


class LUXCORE_PT_material_presets(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Node Tree Presets"

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout

        row = layout.row()

        for category, presets in LUXCORE_OT_preset_material.categories.items():
            col = row.column()
            col.label(category)

            for preset in presets:
                op = col.operator("luxcore.preset_material", text=preset)
                op.preset = preset


class LUXCORE_PT_settings(MaterialButtonsPanel, Panel):
    bl_label = "Settings"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.material and engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        mat = context.material

        if mat.luxcore.auto_vp_color:
            split = layout.split(percentage=0.8)
            split.prop(mat.luxcore, "auto_vp_color")
            row = split.row()
            row.enabled = not mat.luxcore.auto_vp_color
            row.prop(mat, "diffuse_color", text="")
        else:
            layout.prop(mat.luxcore, "auto_vp_color")
            layout.prop(mat, "diffuse_color", text="Viewport Color")


class LUXCORE_PT_material_preview(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Preview"
    bl_options = {"DEFAULT_CLOSED"}

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
