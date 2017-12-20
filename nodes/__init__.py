import bpy
from bpy.types import Node
from .. import utils

TREE_TYPES = (
    "luxcore_material_nodes",
    "luxcore_texture_nodes",
    "luxcore_volume_nodes",
)


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
        # TODO: emission

    def export_common_inputs(self, props, definitions):
        """ Call from derived classes (in export method) """
        transparency = self.inputs["Opacity"].export(props)
        if transparency != 1.0:
            definitions["transparency"] = transparency

        bump = self.inputs["Bump"].export(props)
        if bump:
            definitions["bumptex"] = bump


class LuxCoreNodeTexture(LuxCoreNode):
    """Base class for material nodes"""
    suffix = "tex"
    prefix = "scene.textures."


class LuxCoreNodeVolume(LuxCoreNode):
    """Base class for material nodes"""
    suffix = "vol"
    prefix = "scene.volumes."


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
            node.inputs['U-Roughness'].enabled = node.rough
            node.inputs['V-Roughness'].enabled = node.rough
        else:
            node.inputs['Roughness'].enabled = node.rough

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
    def init(node, default=0.1, init_enabled=True):
        node.add_input("LuxCoreSocketRoughness", "Roughness", default)
        node.inputs["Roughness"].enabled = init_enabled
        node.add_input("LuxCoreSocketRoughness", "V-Roughness", default)
        node.inputs["V-Roughness"].enabled = False

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
