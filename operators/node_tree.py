import bpy
from bpy.props import StringProperty
from .. import utils


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

    def execute(self, context):
        if getattr(context, "material", None):
            name = context.material.name + "_Mat_Nodes"
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

    def execute(self, context):
        name = "Volume Node Tree"
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


def new_node(bl_idname, node_tree, previous_node, output=0, input=0):
    node = node_tree.nodes.new(bl_idname)
    node.location = (previous_node.location.x - 250, previous_node.location.y)
    node_tree.links.new(node.outputs[output], previous_node.inputs[input])
    return node


class LUXCORE_OT_preset_material(bpy.types.Operator):
    bl_idname = "luxcore.preset_material"
    bl_label = ""
    bl_description = "Add a pre-definied node setup"

    basic_mapping = {
        "Mix": "LuxCoreNodeMatMix",
        "Glossy": "LuxCoreNodeMatGlossy2",
        "Glass": "LuxCoreNodeMatGlass",
        "Null (Transparent)": "LuxCoreNodeMatNull",
        "Metal": "LuxCoreNodeMatMetal",
        "Mirror": "LuxCoreNodeMatMirror",
        "Glossy Translucent": "LuxCoreNodeMatGlossyTranslucent",
        "Matte Translucent": "LuxCoreNodeMatMatteTranslucent",
    }

    preset = StringProperty()
    categories = {
        "Basic": list(basic_mapping.keys()),
        "Advanced": [
            "Smoke",
        ],
    }

    @classmethod
    def poll(cls, context):
        return context.object

    def _add_node_tree(self, name):
        node_tree = bpy.data.node_groups.new(name=name, type="luxcore_material_nodes")
        node_tree.use_fake_user = True
        return node_tree

    def execute(self, context):
        mat = context.material
        obj = context.object

        if mat is None:
            # We need to create a material
            mat = bpy.data.materials.new(name="Material")

            # Attach the new material to the active object
            if obj.material_slots:
                obj.material_slots[obj.active_material_index].material = mat
            else:
                obj.data.materials.append(mat)

        # We have a material, but maybe it has no node tree attached
        node_tree = mat.luxcore.node_tree

        if node_tree is None:
            node_tree = self._add_node_tree(mat.name)
            mat.luxcore.node_tree = node_tree

        nodes = node_tree.nodes

        # Add the new nodes below all other nodes
        # x location should be centered (average of other nodes x positions)
        # y location shoud be below all others
        location_x = 300
        location_y = 500

        for node in nodes:
            location_x = max(node.location.x, location_x)
            location_y = min(node.location.y, location_y)
            # De-select all nodes
            node.select = False

        # Create an output for the new nodes
        output = nodes.new("LuxCoreNodeMatOutput")
        output.location = (location_x, location_y - 300)
        output.select = False

        # Category: Basic
        if self.preset in self.basic_mapping:
            new_node(self.basic_mapping[self.preset], node_tree, output)
        # Category: Advanced
        elif self.preset == "Smoke":
            self._preset_smoke(obj, node_tree, output)

        return {"FINISHED"}

    def _preset_smoke(self, obj, node_tree, output):
        # A smoke material setup only makes sense on the smoke domain object
        if not utils.find_smoke_domain_modifier(obj):
            self.report({"ERROR"}, 'Object "%s" is not a smoke domain!' % obj.name)
            return {"CANCELLED"}

        new_node("LuxCoreNodeMatNull", node_tree, output)

        # We need a volume
        name = "Smoke Volume"
        vol_node_tree = bpy.data.node_groups.new(name=name, type="luxcore_volume_nodes")
        vol_nodes = vol_node_tree.nodes
        # Attach to output node
        output.interior_volume = vol_node_tree

        # Add volume nodes
        vol_output = vol_nodes.new("LuxCoreNodeVolOutput")
        vol_output.location = 300, 200

        heterogeneous = new_node("LuxCoreNodeVolHeterogeneous", vol_node_tree, vol_output)
        smoke_node = new_node("LuxCoreNodeTexSmoke", vol_node_tree, heterogeneous, 0, "Scattering")
        smoke_node.domain = obj
        smoke_node.source = "density"
        smoke_node.wrap = "black"
