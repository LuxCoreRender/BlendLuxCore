import bpy
from bpy.props import StringProperty, IntProperty
from .. import utils
from ..nodes import TREE_TYPES, TREE_ICONS
from .utils import (
    poll_object, poll_material, poll_volume, make_nodetree_name,
    init_mat_node_tree, init_tex_node_tree, init_vol_node_tree
)


class LUXCORE_OT_mat_nodetree_new(bpy.types.Operator):
    bl_idname = "luxcore.mat_nodetree_new"
    bl_label = "New"
    bl_description = "Create a material node tree"

    @classmethod
    def poll(cls, context):
        return poll_object(context)

    def execute(self, context):
        if getattr(context, "material", None):
            name = make_nodetree_name(context.material.name)
        else:
            name = "Material Node Tree"

        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_material_nodes")
        init_mat_node_tree(node_tree)

        if getattr(context, "material", None):
            context.material.luxcore.node_tree = node_tree

        return {"FINISHED"}


class LUXCORE_OT_vol_nodetree_new(bpy.types.Operator):
    bl_idname = "luxcore.vol_nodetree_new"
    bl_label = "New"
    bl_description = "Create a volume node tree"

    # The target slot where the new volume should be linked to: "interior_volume" or "exterior_volume"
    target = StringProperty()

    @classmethod
    def poll(cls, context):
        return poll_volume(context)

    def execute(self, context):
        assert self.target in ("interior_volume", "exterior_volume")

        name = ""
        if context.node:
            name = context.node.id_data.name
        name += "_%s_Volume" % self.target.split("_")[0].title()

        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_volume_nodes")
        init_vol_node_tree(node_tree)

        if context.node and hasattr(context.node, self.target):
            context.node[self.target] = node_tree

        return {"FINISHED"}


class LUXCORE_OT_tex_nodetree_new(bpy.types.Operator):
    bl_idname = "luxcore.tex_nodetree_new"
    bl_label = "New"
    bl_description = "Create a texture node tree"

    def execute(self, context):
        name = "Texture Node Tree"
        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_texture_nodes")
        init_tex_node_tree(node_tree)

        return {"FINISHED"}


class LUXCORE_OT_vol_nodetree_unlink(bpy.types.Operator):
    bl_idname = "luxcore.vol_nodetree_unlink"
    bl_label = "Unlink"
    bl_description = "Unlink this volume node tree"

    # The target slot from which the volume should be unlinked: "interior_volume" or "exterior_volume"
    target = StringProperty()

    @classmethod
    def poll(cls, context):
        return poll_volume(context)

    def execute(self, context):
        assert self.target in ("interior_volume", "exterior_volume")

        if context.node and hasattr(context.node, self.target):
            context.node[self.target] = None

        return {"FINISHED"}


class LUXCORE_OT_switch_to_node_tree(bpy.types.Operator):
    """
    Note: this operator only works in layouts of nodes (needs node editor context)
    """

    bl_idname = "luxcore.switch_to_node_tree"
    bl_label = "Show"
    bl_description = "Show node tree"

    name = StringProperty()

    def execute(self, context):
        node_tree = bpy.data.node_groups[self.name]
        space = context.space_data

        space.tree_type = node_tree.bl_idname
        space.node_tree = node_tree

        return {"FINISHED"}


### Node Tree setter operators, used for the dropdown menus that only show one kind of node tree


class LUXCORE_OT_set_node_tree(bpy.types.Operator):
    """ Generic version. There are subclasses for materials and volumes """

    bl_idname = "luxcore.set_node_tree"
    bl_label = ""
    bl_description = "Assign this node tree"

    def set_node_tree(self, datablock, target, prop, node_tree):
        setattr(target, prop, node_tree)

        # Flag datablock for update in viewport render
        datablock.update_tag()

        if (isinstance(datablock, bpy.types.NodeTree)
                and datablock.bl_idname == "luxcore_material_nodes"):
            # Also flag the materials for update
            for mat in bpy.data.materials:
                if mat.luxcore.node_tree is datablock:
                    mat.update_tag()


class LUXCORE_OT_set_mat_node_tree(LUXCORE_OT_set_node_tree):
    """ Dropdown Operator Material version """

    bl_idname = "luxcore.set_mat_node_tree"

    node_tree_index = IntProperty()

    @classmethod
    def poll(cls, context):
        return poll_material(context)

    def execute(self, context):
        mat = context.material
        node_tree = bpy.data.node_groups[self.node_tree_index]
        self.set_node_tree(mat, mat.luxcore, "node_tree", node_tree)
        return {"FINISHED"}



class LUXCORE_OT_set_vol_node_tree(LUXCORE_OT_set_node_tree):
    """ Dropdown Operator Volume version """

    bl_idname = "luxcore.set_vol_node_tree"

    # The target slot where the new volume should be linked to: "interior_volume" or "exterior_volume"
    target = StringProperty()
    node_tree_index = IntProperty()

    @classmethod
    def poll(cls, context):
        return poll_volume(context)

    def execute(self, context):
        assert self.target in ("interior_volume", "exterior_volume")

        node = context.node
        node_tree = bpy.data.node_groups[self.node_tree_index]
        self.set_node_tree(node.id_data, node, self.target, node_tree)
        return {"FINISHED"}


### Dropdown menus that only show one kind of node tree (e.g. only material nodes


class LUXCORE_MT_node_tree(bpy.types.Menu):
    """ Generic version. There are subclasses for materials and volumes """

    bl_idname = "LUXCORE_MT_node_tree"
    bl_label = "Select Node Tree"
    bl_description = "Select a node tree"

    def draw(self, context):
        # Has to be present for class registration
        pass

    def custom_draw(self, tree_type, set_operator, volume_prop=""):
        assert tree_type in TREE_TYPES

        layout = self.layout

        icon = TREE_ICONS[tree_type]
        source = bpy.data.node_groups
        trees = [(i, tree) for i, tree in enumerate(source) if tree.bl_idname == tree_type]

        row = layout.row()
        col = row.column()

        if not trees:
            # No node trees of this type in the scene yet
            tree_type_pretty = tree_type.split("_")[1]
            col.label("No " + tree_type_pretty + " node trees")

            if tree_type == "luxcore_material_nodetree":
                # Volumes need a more complicated new operator (Todo)
                col.operator("luxcore.mat_nodetree_new", text="New Node Tree", icon="ZOOMIN")
                col.menu("LUXCORE_MT_node_tree_preset")

        for j, (i, tree) in enumerate(trees):
            if j > 0 and j % 20 == 0:
                col = row.column()

            text = utils.get_name_with_lib(tree)

            op = col.operator(set_operator, text=text, icon=icon)
            op.node_tree_index = i

            if volume_prop:
                op.target = volume_prop


class LUXCORE_MATERIAL_MT_node_tree(LUXCORE_MT_node_tree):
    """ Dropdown Menu Material version """

    bl_idname = "LUXCORE_MATERIAL_MT_node_tree"
    bl_description = "Select a material node tree"

    @classmethod
    def poll(cls, context):
        return poll_material(context)

    def draw(self, context):
        self.custom_draw("luxcore_material_nodes", "luxcore.set_mat_node_tree")


class LUXCORE_VOLUME_MT_node_tree_interior(LUXCORE_MT_node_tree):
    """ Dropdown Menu Volume version """

    bl_idname = "LUXCORE_VOLUME_MT_node_tree_interior"
    bl_description = "Select a volume node tree"

    @classmethod
    def poll(cls, context):
        return poll_volume(context)

    def draw(self, context):
        self.custom_draw("luxcore_volume_nodes",
                         "luxcore.set_vol_node_tree",
                         "interior_volume")


class LUXCORE_VOLUME_MT_node_tree_exterior(LUXCORE_MT_node_tree):
    """ Dropdown Menu Volume version """

    bl_idname = "LUXCORE_VOLUME_MT_node_tree_exterior"
    bl_description = "Select a volume node tree"

    @classmethod
    def poll(cls, context):
        return poll_volume(context)

    def draw(self, context):
        self.custom_draw("luxcore_volume_nodes",
                         "luxcore.set_vol_node_tree",
                         "exterior_volume")


# TODO: use new dropdowns in pointer node
