import bpy
from bpy.types import Node
from bpy.props import PointerProperty
from .. import utils
from ..utils import node as utils_node
from ..ui import ICON_MATERIAL, ICON_TEXTURE, ICON_VOLUME

TREE_TYPES = (
    "luxcore_material_nodes",
    "luxcore_texture_nodes",
    "luxcore_volume_nodes",
)

TREE_ICONS = {
    "luxcore_material_nodes": ICON_MATERIAL,
    "luxcore_texture_nodes": ICON_TEXTURE,
    "luxcore_volume_nodes": ICON_VOLUME,
}

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

COLORDEPTH_DESC = "Depth at which white light is turned into the absorption color."


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
        return utils.make_key(self)

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
    """Base class for texture nodes"""
    suffix = "tex"
    prefix = "scene.textures."


class LuxCoreNodeVolume(LuxCoreNode):
    """Base class for volume nodes"""
    suffix = "vol"
    prefix = "scene.volumes."

    # Common properties that every derived class needs to add
    # priority (IntProperty)
    # emission_id (IntProperty) (or maybe PointerProperty to light group later)
    # color_depth (FloatProperty) - for implicit colordepth texture

    def draw_common_buttons(self, context, layout):
        layout.prop(self, "priority")
        layout.prop(self, "emission_id")
        layout.prop(self, "color_depth")

    def add_common_inputs(self):
        """ Call from derived classes (in init method) """
        self.add_input("LuxCoreSocketColor", "Absorption", (1, 1, 1))
        self.add_input("LuxCoreSocketIOR", "IOR", 1.5)
        self.add_input("LuxCoreSocketColor", "Emission", (0, 0, 0))
        
    def export_common_inputs(self, props, definitions):
        """ Call from derived classes (in export method) """
        definitions["ior"] = self.inputs["IOR"].export(props)

        abs_col = self.inputs["Absorption"].export(props)

        if self.inputs["Absorption"].is_linked:
            # Implicitly create a colordepth texture with unique name
            tex_name = self.make_name() + "_colordepth"
            helper_prefix = "scene.textures." + tex_name + "."
            helper_defs = {
                "type": "colordepth",
                "kt": abs_col,
                "depth": self.color_depth,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))
            abs_col = tex_name
        else:
            # Do not occur the overhead of the colordepth texture
            abs_col = utils.absorption_at_depth_scaled(abs_col, self.color_depth)

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
        elif self.node_tree:
            # Some unkown or unsupported node tree type, e.g. volumes
            layout.template_ID(self, "node_tree")
            layout.label("Node type not supported!", icon="ERROR")
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
    def has_backface(node):
        return "BF Roughness" in node.inputs or "BF U-Roughness" in node.inputs

    @staticmethod
    def toggle_roughness(node, context):
        """
        Enable/disable all roughness inputs.
        Currently only used by glass node.

        Strictly speaking we don't need backface support here,
        but add it anyway in case we have a material in the
        future that has backface and needs roughness on/off switch.
        """
        sockets = ["U-Roughness", "V-Roughness", "Roughness"]
        # Back face variants
        for socket in sockets.copy():
            sockets.append("BF " + socket)

        for socket in sockets:
            try:
                node.inputs[socket].enabled = node.rough
            except KeyError:
                pass

    @staticmethod
    def update_anisotropy(node, context):
        def update(node, is_backface):
            if is_backface:
                roughness = "BF Roughness"
                u_roughness = "BF U-Roughness"
                v_roughness = "BF V-Roughness"
                extra_check = node.use_backface
            else:
                roughness = "Roughness"
                u_roughness = "U-Roughness"
                v_roughness = "V-Roughness"
                extra_check = True

            if roughness in node.inputs:
                u_roughness_input = node.inputs[roughness]
            else:
                u_roughness_input = node.inputs[u_roughness]
            u_roughness_input.name = u_roughness if node.use_anisotropy else roughness
            node.inputs[v_roughness].enabled = node.use_anisotropy and extra_check

        update(node, False)
        if Roughness.has_backface(node):
            update(node, True)

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
    def init_backface(node, default=0.05, init_enabled=True):
        node.add_input("LuxCoreSocketRoughness", "BF Roughness", default)
        node.inputs["BF Roughness"].enabled = init_enabled
        node.add_input("LuxCoreSocketRoughness", "BF V-Roughness", default)
        node.inputs["BF V-Roughness"].enabled = False

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

        if Roughness.has_backface(node):
            if node.use_anisotropy:
                uroughness = node.inputs["BF U-Roughness"].export(props)
                vroughness = node.inputs["BF V-Roughness"].export(props)
            else:
                uroughness = node.inputs["BF Roughness"].export(props)
                vroughness = uroughness

            definitions["uroughness_bf"] = uroughness
            definitions["vroughness_bf"] = vroughness
