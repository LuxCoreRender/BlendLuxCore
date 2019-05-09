import bpy
from bpy.types import Node
from bpy.props import PointerProperty, EnumProperty
from .. import utils
from ..utils import node as utils_node
from ..utils import ui as utils_ui
from ..ui import icons

TREE_TYPES = (
    "luxcore_material_nodes",
    "luxcore_texture_nodes",
    "luxcore_volume_nodes",
)

TREE_ICONS = {
    "luxcore_material_nodes": icons.NTREE_MATERIAL,
    "luxcore_texture_nodes": icons.NTREE_TEXTURE,
    "luxcore_volume_nodes": icons.NTREE_VOLUME,
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

COLORDEPTH_DESC = "Depth at which white light is turned into the absorption color"


class LuxCoreNodeTree:
    """Base class for LuxCore node trees"""
    requested_links = set()

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def update(self):
        # Create all links that were requested by insert_link method calls of nodes
        # (this happens when a link is dragged onto an existing link and the node
        # has other suitable sockets where the original link can be moved to)
        for from_socket, to_socket in self.requested_links:
            self.links.new(from_socket, to_socket)
        self.requested_links.clear()

        # We have to force an update through a Blender property, otherwise the
        # material preview, the viewport render etc. do not update
        self.refresh = True

    def acknowledge_connection(self, context):
        # Set refresh to False without triggering acknowledge_connection again
        self["refresh"] = False

    refresh = bpy.props.BoolProperty(default=False,
                                     update=acknowledge_connection)


class LuxCoreNode(Node):
    """Base class for LuxCore nodes (material, volume and texture)"""
    bl_label = ""

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname in TREE_TYPES

    def insert_link(self, link):
        # Note that this function is called BEFORE the new link is inserted into the node tree.
        node_tree = self.id_data

        for old_link in node_tree.links:
            # Check if an old link is deleted by this new link
            if old_link.to_socket == link.to_socket:
                if not old_link.from_socket.enabled:
                    # Links from disabled sockets are not visible to the user, but prevent
                    # other links from being established. This code solves this problem.
                    # Sockets can be disabled on nodes where there are multiple output
                    # sockets, e.g. the pointer node (Material/Volume/Color output, depending
                    # on the selected node tree)
                    node_tree.requested_links.add((link.from_socket, link.to_socket))
                    break

                # Try to find a suitable replacement socket (e.g. switch from "Material 1"
                # to "Material 2" on the Mix node, if "Material 2" is free)
                for socket in link.to_node.inputs:
                    if socket.bl_idname == link.to_socket.bl_idname and not socket.is_linked:
                        # We can not create the new link directly in this method, instead
                        # the node_tree will create all requested links in its update method
                        node_tree.requested_links.add((old_link.from_socket, socket))
                        break

    def add_input(self, type, name, default=None):
        input = self.inputs.new(type, name)

        if hasattr(input, "default_value"):
            input.default_value = default

        return input

    def make_name(self):
        return utils.make_key(self)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        raise NotImplementedError("Subclasses have to implement this method!")

    def export(self, exporter, props, luxcore_name=None, output_socket=None):
        """ This method is an abstraction layer that handles the caching. """
        cache_key = self.make_name()
        if output_socket:
            cache_key += utils.sanitize_luxcore_name(output_socket.name)

        if luxcore_name is None:
            luxcore_name = cache_key

        if cache_key in exporter.node_cache:
            return exporter.node_cache[cache_key]
        else:
            # Nodes can return a different luxcore_name than the one that
            # is passed in to sub_export, for example when an implicit scale
            # texture is added.
            luxcore_name = self.sub_export(exporter, props, luxcore_name, output_socket)
            exporter.node_cache[cache_key] = luxcore_name
            return luxcore_name

    def create_props(self, props, definitions, luxcore_name):
        prefix = self.prefix + luxcore_name + "."
        props.Set(utils.create_props(prefix, definitions))
        return luxcore_name

    def free(self):
        # This method implements a workaround to have "delete and reconnect" functionality.
        node_tree = self.id_data

        for input in self.inputs:
            for output in self.outputs:
                if input.links and output.links:
                    from_socket = input.links[0].from_socket

                    for link in output.links:
                        to_socket = link.to_socket

                        if utils_node.is_allowed_input(to_socket, from_socket):
                            node_tree.links.new(from_socket, to_socket)


class LuxCoreNodeMaterial(LuxCoreNode):
    """Base class for material nodes"""
    suffix = "mat"
    prefix = "scene.materials."

    def add_common_inputs(self):
        """ Call from derived classes (in init method) """
        self.add_input("LuxCoreSocketFloat0to1", "Opacity", 1)
        self.add_input("LuxCoreSocketBump", "Bump")
        self.add_input("LuxCoreSocketMatEmission", "Emission")

    def export_common_inputs(self, exporter, props, definitions):
        """ Call from derived classes (in export method) """
        transparency = self.inputs["Opacity"].export(exporter, props)
        if transparency != 1.0:
            definitions["transparency"] = transparency

        bump = self.inputs["Bump"].export(exporter, props)
        if bump:
            definitions["bumptex"] = bump

        # The emission socket and node are special cases
        # with special export methods
        self.inputs["Emission"].export_emission(exporter, props, definitions)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        raise NotImplementedError("Subclasses have to implement this method!")


class LuxCoreNodeTexture(LuxCoreNode):
    """Base class for texture nodes"""
    suffix = "tex"
    prefix = "scene.textures."

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        raise NotImplementedError("Subclasses have to implement this method!")


class LuxCoreNodeVolume(LuxCoreNode):
    """Base class for volume nodes"""
    suffix = "vol"
    prefix = "scene.volumes."

    # Common properties that every derived class needs to add
    # priority (IntProperty)
    # color_depth (FloatProperty) - for implicit colordepth texture
    # lightgroup (StringProperty)

    def draw_common_buttons(self, context, layout):
        layout.prop(self, "priority")
        lightgroups = context.scene.luxcore.lightgroups
        layout.prop_search(self, "lightgroup",
                           lightgroups, "custom",
                           icon=icons.LIGHTGROUP, text="")
        layout.prop(self, "color_depth")

    def add_common_inputs(self):
        """ Call from derived classes (in init method) """
        self.add_input("LuxCoreSocketColor", "Absorption", (1, 1, 1))
        self.add_input("LuxCoreSocketIOR", "IOR", 1.5)
        self.add_input("LuxCoreSocketColor", "Emission", (0, 0, 0))
        
    def export_common_inputs(self, exporter, props, definitions):
        """ Call from derived classes (in export method) """
        definitions["ior"] = self.inputs["IOR"].export(exporter, props)
        definitions["priority"] = self.priority

        abs_col = self.inputs["Absorption"].export(exporter, props)
        worldscale = utils.get_worldscale(exporter.scene, as_scalematrix=False)
        abs_depth = self.color_depth * worldscale

        if self.inputs["Absorption"].is_linked:
            # Implicitly create a colordepth texture with unique name
            tex_name = self.make_name() + "_colordepth"
            helper_prefix = "scene.textures." + tex_name + "."
            helper_defs = {
                "type": "colordepth",
                "kt": abs_col,
                "depth": abs_depth,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))
            abs_col = tex_name
        else:
            # Do not occur the overhead of the colordepth texture
            abs_col = utils.absorption_at_depth_scaled(abs_col, abs_depth)

        if "Scattering" in self.inputs:
            scattering_col = self.export_scattering(exporter, props)
            definitions["scattering"] = scattering_col

        definitions["absorption"] = abs_col
        definitions["emission"] = self.inputs["Emission"].export(exporter, props)

        lightgroups = exporter.scene.luxcore.lightgroups
        lightgroup_id = lightgroups.get_id_by_name(self.lightgroup)
        definitions["emission.id"] = lightgroup_id
        exporter.lightgroup_cache.add(lightgroup_id)

    def export_scattering(self, exporter, props):
        scattering_col_socket = self.inputs["Scattering"]
        scattering_scale_socket = self.inputs["Scattering Scale"]

        scattering_col = scattering_col_socket.export(exporter, props)
        scattering_scale = scattering_scale_socket.export(exporter, props)

        if scattering_scale_socket.is_linked or scattering_col_socket.is_linked:
            # Implicitly create a colordepth texture with unique name
            tex_name = self.make_name() + "_scale"
            helper_prefix = "scene.textures." + tex_name + "."
            helper_defs = {
                "type": "scale",
                "texture1": scattering_scale,
                "texture2": scattering_col,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))
            scattering_col = tex_name
        else:
            # We do not have to use a texture - improves performance
            for i in range(len(scattering_col)):
                scattering_col[i] *= scattering_scale

        return scattering_col

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        raise NotImplementedError("Subclasses have to implement this method!")


class LuxCoreNodeTreePointer(LuxCoreNode):
    """ Pointer to a node tree """
    bl_label = "Pointer"
    bl_width_default = 250
    suffix = "pointer"

    def update_node_tree(self, context):
        if self.node_tree:
            self.outputs["Material"].enabled = self.node_tree.bl_idname == "luxcore_material_nodes"
            self.outputs["Color"].enabled = self.node_tree.bl_idname == "luxcore_texture_nodes"
            self.outputs["Volume"].enabled = self.node_tree.bl_idname == "luxcore_volume_nodes"
        else:
            self.outputs["Material"].enabled = False
            self.outputs["Color"].enabled = False
            self.outputs["Volume"].enabled = False

    node_tree = PointerProperty(name="Node Tree", type=bpy.types.NodeTree, update=update_node_tree,
                                description="Use the output of the selected node tree in this node tree")

    filter_items = [
        ("luxcore_material_nodes", "Materials", "Only show material nodes", icons.NTREE_MATERIAL, 0),
        ("luxcore_volume_nodes", "Volumes", "Only show volume nodes", icons.NTREE_VOLUME, 1),
        ("luxcore_texture_nodes", "Textures", "Only show texture nodes", icons.NTREE_TEXTURE, 2),
    ]
    filter = EnumProperty(name="Filter", items=filter_items, default="luxcore_volume_nodes",
                          description="Filter for the node tree selection menu below")

    def init(self, context):
        self.outputs.new("LuxCoreSocketMaterial", "Material")
        self.outputs["Material"].enabled = False
        self.outputs.new("LuxCoreSocketColor", "Color")
        self.outputs["Color"].enabled = False
        self.outputs.new("LuxCoreSocketVolume", "Volume")
        self.outputs["Volume"].enabled = False

    def draw_label(self):
        if self.node_tree:
            return 'Pointer to "%s"' % self.node_tree.name
        else:
            return self.bl_label

    def draw_buttons(self, context, layout):
        layout.prop(self, "filter", expand=True)

        if self.node_tree:
            icon = TREE_ICONS[self.node_tree.bl_idname]
        else:
            icon = "NODETREE"

        utils_ui.template_node_tree(layout, self, "node_tree", icon,
                                    "LUXCORE_MT_pointer_select_node_tree",
                                    "luxcore.pointer_show_node_tree",
                                    "",  # Do not offer to create a node tree
                                    "luxcore.pointer_unlink_node_tree")

        if self.node_tree == self.id_data:
            layout.label("Recursion!", icon=icons.WARNING)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        if self.node_tree == self.id_data:
            raise Exception("Recursion (pointer referencing its own node tree)")

        # Import statement here to prevent circular imports
        from .output import get_active_output
        output = get_active_output(self.node_tree)

        if output is None:
            print("ERROR: no active output found in node tree", self.node_tree.name)
            return None

        # Ignore the passed-in luxcore_name here.
        # Not a shader instance (if we ever support inputs, we will need to make
        # different shader instances for different sets of input parameters)
        luxcore_name = utils.get_luxcore_name(self.node_tree)

        output.export(exporter, props, luxcore_name)
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
        Roughness.update_anisotropy(node, context)

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
    def export(node, exporter, props, definitions):
        if node.use_anisotropy:
            uroughness = node.inputs["U-Roughness"].export(exporter, props)
            vroughness = node.inputs["V-Roughness"].export(exporter, props)
        else:
            uroughness = node.inputs["Roughness"].export(exporter, props)
            vroughness = uroughness

        definitions["uroughness"] = uroughness
        definitions["vroughness"] = vroughness

        if Roughness.has_backface(node):
            if node.use_anisotropy:
                uroughness = node.inputs["BF U-Roughness"].export(exporter, props)
                vroughness = node.inputs["BF V-Roughness"].export(exporter, props)
            else:
                uroughness = node.inputs["BF Roughness"].export(exporter, props)
                vroughness = uroughness

            definitions["uroughness_bf"] = uroughness
            definitions["vroughness_bf"] = vroughness
