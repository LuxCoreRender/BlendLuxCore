import bpy
from bpy.props import IntProperty, StringProperty
from .utils import poll_object, make_nodetree_name, init_mat_node_tree
from .. import utils


class LUXCORE_OT_material_new(bpy.types.Operator):
    bl_idname = "luxcore.material_new"
    bl_label = "New"
    bl_description = "Create a new material and node tree"

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

        return {"FINISHED"}


class LUXCORE_OT_material_copy(bpy.types.Operator):
    bl_idname = "luxcore.material_copy"
    bl_label = "Copy"
    bl_description = "Create a copy of the material (also copying the nodetree)"

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

    material_index = IntProperty()

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        mat = bpy.data.materials[self.material_index]
        context.object.active_material = mat

        return {"FINISHED"}


class LUXCORE_MT_material_select(bpy.types.Menu):
    bl_label = "Select Material"
    bl_description = "Select a material"

    def draw(self, context):
        layout = self.layout

        if not bpy.data.materials:
            layout.label("No materials available")

        row = layout.row()
        col = row.column()

        for i in range(len(bpy.data.materials)):
            if i > 0 and i % 15 == 0:
                col = row.column()

            mat = bpy.data.materials[i]
            name = utils.get_name_with_lib(mat)

            op = col.operator("luxcore.material_set", text=name, icon="MATERIAL")
            op.material_index = i
