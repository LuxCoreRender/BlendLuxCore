import bpy
from bpy.types import Node
from bpy.props import PointerProperty
from .. import utils
import math
from ..utils import node as utils_node

TREE_TYPES = (
    "luxcore_material_nodes",
    "luxcore_texture_nodes",
    "luxcore_volume_nodes",
)

NOISE_BASIS_ITEMS = [
    ("blender_original", "Blender Original", ""),
    ("original_perlin", "Original Perlin", ""),
    ("improved_perlin", "Improved Perlin", ""),
    ("voronoi_f1", "Voronoi F1", ""),
    ("voronoi_f2", "Voronoi F2", ""),
    ("voronoi_f3", "Voronoi F3", ""),
    ("voronoi_f4", "Voronoi F4", ""),
    ("voronoi_f2f1", "Voronoi F2-F1", ""),
    ("voronoi_crackle", "Voronoi Crackle", ""),
    ("cell_noise", "Cell Noise", ""),
]

NOISE_TYPE_ITEMS = [
    ("soft_noise", "Soft", ""),
    ("hard_noise", "Hard", "")
]


class LuxCoreNode(Node):
    """Base class for LuxCore nodes (material, volume and texture)"""
    bl_label = ""

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname in TREE_TYPES

    def add_input(self, type, name, default=None):
        self.inputs.new(type, name)

        if hasattr(self.inputs[name], "default_value"):
            self.inputs[name].default_value = default

    def make_name(self):
        node_tree = self.id_data
        name_parts = [self.name, node_tree.name, self.suffix]

        if node_tree.library:
            name_parts.append(node_tree.library.name)

        return utils.to_luxcore_name("_".join(name_parts))

    def base_export(self, props, definitions, luxcore_name=None):
        if luxcore_name is None:
            luxcore_name = self.make_name()

        prefix = self.prefix + luxcore_name + "."
        props.Set(utils.create_props(prefix, definitions))
        return luxcore_name


class LuxCoreNodeMaterial(LuxCoreNode):
    """Base class for material nodes"""
    suffix = "mat"
    prefix = "scene.materials."

    def add_common_inputs(self):
        """ Call from derived classes (in init method) """
        self.add_input("LuxCoreSocketFloat0to1", "Opacity", 1)
        self.add_input("LuxCoreSocketBump", "Bump")
        self.add_input("LuxCoreSocketMatEmission", "Emission")

    def export_common_inputs(self, props, definitions):
        """ Call from derived classes (in export method) """
        transparency = self.inputs["Opacity"].export(props)
        if transparency != 1.0:
            definitions["transparency"] = transparency

        bump = self.inputs["Bump"].export(props)
        if bump:
            definitions["bumptex"] = bump

        # The emission socket and node are special cases
        # with special export methods
        self.inputs["Emission"].export_emission(props, definitions)


class LuxCoreNodeTexture(LuxCoreNode):
    """Base class for material nodes"""
    suffix = "tex"
    prefix = "scene.textures."


class LuxCoreNodeVolume(LuxCoreNode):
    """Base class for material nodes"""
    suffix = "vol"
    prefix = "scene.volumes."

    # Common properties that every derived class needs to add
    # priority (IntProperty)
    # emission_id (IntProperty) (or maybe PointerProperty to light group later)

    def draw_common_buttons(self, context, layout):
        layout.prop(self, "priority")
        layout.prop(self, "emission_id")

    def add_common_inputs(self):
        """ Call from derived classes (in init method) """
        self.add_input("LuxCoreSocketIOR", "IOR", 1.5)
        self.add_input("LuxCoreSocketColor", "Absorption", (1, 1, 1))
        self.add_input("LuxCoreSocketValueAtDepth", "Absorption at depth", 1.0)
        self.add_input("LuxCoreSocketFloatPositive", "Absorption scale", 1.0)
        self.add_input("LuxCoreSocketColor", "Emission", (0, 0, 0))
        
    def export_common_inputs(self, props, definitions):
        """ Call from derived classes (in export method) """
        definitions["ior"] = self.inputs["IOR"].export(props)

        abs_col = self.inputs["Absorption"].export(props)

        for i in range(len(abs_col)):
            v = float(abs_col[i])
            depth = self.inputs["Absorption at depth"].export(props)
            scale = self.inputs["Absorption scale"].export(props)
            abs_col[i] = (-math.log(max([v, 1e-30])) / depth) * scale * (v == 1.0 and -1 or 1)

        definitions["absorption"] = abs_col
        definitions["emission"] = self.inputs["Emission"].export(props)


class LuxCoreNodeTreePointer(LuxCoreNode):
    """ Pointer to a node tree """
    bl_label = "Pointer"
    bl_width_min = 160
    suffix = "pointer"

    def update_node_tree(self, context):
        if self.node_tree:
            self.outputs["Material"].enabled = self.node_tree.bl_idname == "luxcore_material_nodes"
            self.outputs["Color"].enabled = self.node_tree.bl_idname == "luxcore_texture_nodes"
        else:
            self.outputs["Material"].enabled = False
            self.outputs["Color"].enabled = False

    node_tree = PointerProperty(name="Node Tree", type=bpy.types.NodeTree, update=update_node_tree)

    def init(self, context):
        self.outputs.new("LuxCoreSocketMaterial", "Material")
        self.outputs["Material"].enabled = False
        self.outputs.new("LuxCoreSocketColor", "Color")
        self.outputs["Color"].enabled = False

    def draw_buttons(self, context, layout):
        # TODO the new operators don't link the created node tree to self.node_tree
        if self.node_tree and self.node_tree.bl_idname == "luxcore_material_nodes":
            layout.template_ID(self, "node_tree", new="luxcore.mat_nodetree_new")
        elif self.node_tree and self.node_tree.bl_idname == "luxcore_texture_nodes":
            layout.template_ID(self, "node_tree", new="luxcore.tex_nodetree_new")
        else:
            row = layout.row()
            row.label("Node Tree:")
            row.template_ID(self, "node_tree")

    def export(self, props, luxcore_name=None):
        # Import statement here to prevent circular imports
        from .output import get_active_output
        output = get_active_output(self.node_tree)

        if output is None:
            print("ERROR: no active output found in node tree", self.node_tree.name)
            return None

        if luxcore_name is None:
            luxcore_name = self.make_name()

        output.export(props, luxcore_name)
        return luxcore_name


class Roughness:
    """
    How to use this class:
    Declare a use_anisotropy property like this:
    use_anisotropy = BoolProperty(name=Roughness.aniso_name,
                                  default=False,
                                  description=Roughness.aniso_desc,
                                  update=Roughness.update_anisotropy)

    Call Roughness.init(self, default=0.1) in the init method of the material node

    Draw the use_anisotropy property in the draw_buttons method:
    layout.prop(self, "use_anisotropy")

    For an example, see the glossy2 node
    """

    @staticmethod
    def toggle_roughness(node, context):
        """ Enable/disable all roughness inputs """
        if node.use_anisotropy:
            node.inputs["U-Roughness"].enabled = node.rough
            node.inputs["V-Roughness"].enabled = node.rough
        else:
            node.inputs["Roughness"].enabled = node.rough

    @staticmethod
    def update_anisotropy(node, context):
        if "Roughness" in node.inputs:
            u_roughness = node.inputs["Roughness"]
        else:
            u_roughness = node.inputs["U-Roughness"]
        u_roughness.name = "U-Roughness" if node.use_anisotropy else "Roughness"
        node.inputs["V-Roughness"].enabled = node.use_anisotropy

    aniso_name = "Anisotropic Roughness"
    aniso_desc = ("Use different roughness values for "
                 "U- and V-directions (needs UV mapping)")

    @staticmethod
    def init(node, default=0.05, init_enabled=True):
        node.add_input("LuxCoreSocketRoughness", "Roughness", default)
        node.inputs["Roughness"].enabled = init_enabled
        node.add_input("LuxCoreSocketRoughness", "V-Roughness", default)
        node.inputs["V-Roughness"].enabled = False

    @staticmethod
    def draw(node, context, layout):
        layout.prop(node, "use_anisotropy")
        if node.use_anisotropy:
            utils_node.draw_uv_info(context, layout)

    @staticmethod
    def export(node, props, definitions):
        if node.use_anisotropy:
            uroughness = node.inputs["U-Roughness"].export(props)
            vroughness = node.inputs["V-Roughness"].export(props)
        else:
            uroughness = node.inputs["Roughness"].export(props)
            vroughness = uroughness

        definitions["uroughness"] = uroughness
        definitions["vroughness"] = vroughness
