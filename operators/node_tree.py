import bpy
from bpy.props import StringProperty, IntProperty
from .. import utils
from ..nodes import TREE_TYPES, TREE_ICONS


def make_nodetree_name(material_name):
    return "Nodes_" + material_name


def poll_volume(context):
    # Volume node trees are attached to a material output node
    if not hasattr(context, "node"):
        return False
    return context.node and not context.node.id_data.library


def poll_object(context):
    return context.object and not context.object.library


def poll_material(context):
        if not hasattr(context, "material"):
            return False
        return context.material and not context.material.library


def init_mat_node_tree(node_tree):
    # Seems like we still need this.
    # User counting does not work reliably with Python PointerProperty.
    # Sometimes, the material this tree is linked to is not counted as user.
    node_tree.use_fake_user = True

    nodes = node_tree.nodes

    output = nodes.new("LuxCoreNodeMatOutput")
    output.location = 300, 200
    output.select = False

    matte = nodes.new("LuxCoreNodeMatMatte")
    matte.location = 50, 200

    node_tree.links.new(matte.outputs[0], output.inputs[0])


def init_tex_node_tree(node_tree):
    # Seems like we still need this.
    # User counting does not work reliably with Python PointerProperty.
    # Sometimes, the material this tree is linked to is not counted as user.
    node_tree.use_fake_user = True

    nodes = node_tree.nodes

    output = nodes.new("LuxCoreNodeTexOutput")
    output.location = 300, 200
    output.select = False


def init_vol_node_tree(node_tree):
    # Seems like we still need this.
    # User counting does not work reliably with Python PointerProperty.
    # Sometimes, the material this tree is linked to is not counted as user.
    node_tree.use_fake_user = True

    nodes = node_tree.nodes

    output = nodes.new("LuxCoreNodeVolOutput")
    output.location = 300, 200
    output.select = False

    clear = nodes.new("LuxCoreNodeVolClear")
    clear.location = 50, 200

    node_tree.links.new(clear.outputs[0], output.inputs[0])


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


class LUXCORE_OT_switch_to_node_tree(bpy.types.Operator):
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

            text = utils.get_tree_name_with_lib(tree)

            op = col.operator(set_operator, text=text, icon=icon)
            op.node_tree_index = i

            if volume_prop:
                print(volume_prop)
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
