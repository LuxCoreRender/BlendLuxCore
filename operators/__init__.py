import bpy


def init_mat_node_tree(node_tree):
    nodes = node_tree.nodes

    output = nodes.new("LuxCoreNodeMatOutput")
    output.location = 300, 200
    output.select = False

    matte = nodes.new("LuxCoreNodeMatMatte")
    matte.location = 50, 200

    node_tree.links.new(matte.outputs[0], output.inputs[0])


def init_vol_node_tree(node_tree):
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

    def execute(self, context):
        if context.material:
            name = context.material.name + "_Mat_Nodes"
        else:
            name = "Material Node Tree"

        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_material_nodes")
        init_mat_node_tree(node_tree)

        if context.material:
            context.material.luxcore.node_tree = node_tree

        return {"FINISHED"}


class LUXCORE_OT_vol_nodetree_new(bpy.types.Operator):
    bl_idname = "luxcore.vol_nodetree_new"
    bl_label = "New"
    bl_description = "Create a volume node tree"

    # The target slot where the new volume should be linked to: "interior_volume" or "exterior_volume"
    target = bpy.props.StringProperty()

    def execute(self, context):
        name = "Volume Node Tree"
        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_volume_nodes")
        init_vol_node_tree(node_tree)

        if context.node and hasattr(context.node, self.target):
            context.node[self.target] = node_tree

        return {"FINISHED"}


class LUXCORE_OT_material_new(bpy.types.Operator):
    bl_idname = "luxcore.material_new"
    bl_label = "New"
    bl_description = "Create a material and node tree"

    def execute(self, context):
        mat = bpy.data.materials.new(name="Material")
        node_tree = bpy.data.node_groups.new(name=mat.name, type="luxcore_material_nodes")
        init_mat_node_tree(node_tree)
        mat.luxcore.node_tree = node_tree

        obj = context.active_object
        if obj.material_slots:
            obj.material_slots[obj.active_material_index].material = mat
        else:
            obj.data.materials.append(mat)

        return {"FINISHED"}
