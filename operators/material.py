import bpy
from bpy.props import IntProperty, StringProperty, EnumProperty
from .. import utils
from .utils import (
    poll_object, poll_material, init_mat_node_tree, make_nodetree_name,
    LUXCORE_OT_set_node_tree, LUXCORE_MT_node_tree, show_nodetree,
)
from ..ui import icons


class LUXCORE_OT_material_new(bpy.types.Operator):
    bl_idname = "luxcore.material_new"
    bl_label = "New"
    bl_description = "Create a new material and node tree"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        mat = bpy.data.materials.new(name="Material")
        tree_name = make_nodetree_name(mat.name)
        node_tree = bpy.data.node_groups.new(name=tree_name, type="luxcore_material_nodes")
        init_mat_node_tree(node_tree)
        mat.luxcore.node_tree = node_tree

        obj = context.active_object
        if obj.material_slots:
            obj.material_slots[obj.active_material_index].material = mat
        else:
            obj.data.materials.append(mat)

        # For viewport render, we have to update the luxcore object
        # because the newly created material is not yet assigned there
        obj.update_tag()
        show_nodetree(context, node_tree)

        return {"FINISHED"}


class LUXCORE_OT_material_unlink(bpy.types.Operator):
    bl_idname = "luxcore.material_unlink"
    bl_label = ""
    bl_description = "Unlink data-block"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        obj = context.active_object
        if obj.material_slots:
            obj.material_slots[obj.active_material_index].material = None
        return {"FINISHED"}


class LUXCORE_OT_material_copy(bpy.types.Operator):
    bl_idname = "luxcore.material_copy"
    bl_label = "Copy"
    bl_description = "Create a copy of the material (also copying the nodetree)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        current_mat = context.active_object.active_material

        # Create a copy of the material
        new_mat = current_mat.copy()

        current_node_tree = current_mat.luxcore.node_tree

        if current_node_tree:
            # Create a copy of the node_tree as well
            new_node_tree = current_node_tree.copy()
            new_node_tree.name = make_nodetree_name(new_mat.name)
            new_node_tree.use_fake_user = True
            # Assign new node_tree to the new material
            new_mat.luxcore.node_tree = new_node_tree

        context.active_object.active_material = new_mat

        return {"FINISHED"}


class LUXCORE_OT_material_set(bpy.types.Operator):
    bl_idname = "luxcore.material_set"
    bl_label = ""
    bl_description = "Assign this node tree"
    bl_options = {"UNDO"}

    material_index: IntProperty()

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        mat = bpy.data.materials[self.material_index]
        context.object.active_material = mat

        return {"FINISHED"}


class LUXCORE_MT_material_select(bpy.types.Menu):
    """ Old material selection dropdown without search (TODO: remove?) """
    bl_label = "Select Material"
    bl_description = "Select a material"

    def draw(self, context):
        layout = self.layout

        if not bpy.data.materials:
            layout.label(text="No materials available")

        row = layout.row()
        col = row.column()

        mat_count = len(bpy.data.materials)
        entries_per_column = 15

        for i in range(mat_count):
            if mat_count < 50 and i > 0 and i % entries_per_column == 0:
                # Make a new column to the right instead of creating a huge list
                # If we have many materials, we can't do this, because it removes
                # the ability to scroll through the menu if there are more
                # entries than fit on the screen.
                col = row.column()

            mat = bpy.data.materials[i]
            name = utils.get_name_with_lib(mat)

            op = col.operator("luxcore.material_set", text=name, icon=icons.MATERIAL)
            op.material_index = i


class LUXCORE_OT_material_select(bpy.types.Operator):
    """ Material selection dropdown with search feature """
    bl_idname = "luxcore.material_select"
    bl_label = ""
    bl_property = "material"

    callback_strings = []

    def callback(self, context):
        items = []

        for index, mat in enumerate(bpy.data.materials):
            name = utils.get_name_with_lib(mat)
            # We can not show descriptions or icons here unfortunately
            items.append((str(index), name, ""))

        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        LUXCORE_OT_material_select.callback_strings = items
        return items

    material: EnumProperty(name="Materials", items=callback)

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        # Get the index of the selected material
        mat_index = int(self.material)
        mat = bpy.data.materials[mat_index]
        context.object.active_material = mat
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


# Node tree related operators


class LUXCORE_OT_material_show_nodetree(bpy.types.Operator):
    bl_idname = "luxcore.material_show_nodetree"
    bl_label = "Show Nodes"
    bl_description = "Switch to the node tree of this material"

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False

        mat = obj.active_material
        if not mat:
            return False

        if mat.luxcore.use_cycles_nodes:
            return mat.node_tree
        else:
            return mat.luxcore.node_tree

    def execute(self, context):
        mat = context.active_object.active_material
        node_tree = mat.node_tree if mat.luxcore.use_cycles_nodes else mat.luxcore.node_tree

        if show_nodetree(context, node_tree):
            return {"FINISHED"}

        self.report({"ERROR"}, "Open a node editor first")
        return {"CANCELLED"}


class LUXCORE_OT_mat_nodetree_new(bpy.types.Operator):
    bl_idname = "luxcore.mat_nodetree_new"
    bl_label = "New"
    bl_description = "Create a material node tree"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        mat = context.object.active_material
        if mat:
            name = make_nodetree_name(mat.name)
        else:
            name = "Material Node Tree"

        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_material_nodes")
        init_mat_node_tree(node_tree)

        if mat:
            mat.luxcore.node_tree = node_tree

        show_nodetree(context, node_tree)
        return {"FINISHED"}


class LUXCORE_OT_set_mat_node_tree(bpy.types.Operator, LUXCORE_OT_set_node_tree):
    """ Dropdown Operator Material version """

    bl_idname = "luxcore.set_mat_node_tree"

    node_tree_index: IntProperty()

    @classmethod
    def poll(cls, context):
        return poll_material(context)

    def execute(self, context):
        mat = context.material
        node_tree = bpy.data.node_groups[self.node_tree_index]
        self.set_node_tree(mat, mat.luxcore, "node_tree", node_tree)
        return {"FINISHED"}


# Note: this is a menu, not an operator
class LUXCORE_MATERIAL_MT_node_tree(bpy.types.Menu, LUXCORE_MT_node_tree):
    """ Dropdown Menu Material version """

    bl_idname = "LUXCORE_MATERIAL_MT_node_tree"
    bl_description = "Select a material node tree"

    @classmethod
    def poll(cls, context):
        return poll_material(context)

    def draw(self, context):
        self.custom_draw("luxcore_material_nodes", "luxcore.set_mat_node_tree")
