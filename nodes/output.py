import bpy
from .base import LuxCoreNode
from .. import utils
from ..utils import node as utils_node

OUTPUT_MAP = {
    "luxcore_material_nodes": "LuxCoreNodeMatOutput",
    "luxcore_texture_nodes": "LuxCoreNodeTexOutput",
    "luxcore_volume_nodes": "LuxCoreNodeVolOutput",
}


def get_active_output(node_tree):
    output_type = OUTPUT_MAP[node_tree.bl_idname]

    for node in node_tree.nodes:
        node_type = getattr(node, "bl_idname", None)

        if node_type == output_type and node.active:
            return node


def get_output_nodes(node_tree):
    """ Return a list with all output nodes in a node tree """
    output_type = OUTPUT_MAP[node_tree.bl_idname]
    nodes = []

    for node in node_tree.nodes:
        node_type = getattr(node, "bl_idname", None)
        if node_type == output_type:
            nodes.append(node)
    return nodes


def update_active(output_node, context):
    output_node.set_active(output_node.active)
    if not output_node.active:
        # enabled -> disabled is not allowed
        # TODO: allow it, but make it toggle back to the last active output
        output_node.set_active(True)
        return

    output_node.disable_other_outputs()
    utils_node.update_opengl_materials(None, context)


class LuxCoreNodeOutput(LuxCoreNode):
    """
    Output classes for material, texture and volume node trees are derived from this class.
    Only one output node should be active at any time (this class handles that).
    """
    bl_width_default = 160

    def init(self, context):
        self.disable_other_outputs()
        self.set_active(True)
        self.use_custom_color = True

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        layout.prop(self, "active")

    def copy(self, orig_node):
        self.disable_other_outputs()

    def free(self):
        if not self.active:
            # Nothing to do
            return

        node_tree = self.id_data

        for node in get_output_nodes(node_tree):
            if node == self:
                continue
            node.set_active(True)
            # There can only be one active output at a time, so
            # we don't need to check the others
            break

    def export(self, exporter, depsgraph, props, luxcore_name):
        raise NotImplementedError("Subclasses have to override this method!")

    def set_active(self, active):
        self["active"] = active

        # Update color
        theme = utils.get_theme(bpy.context)
        # We can only set a tuple with 3 elements, not 4
        color = theme.node_editor.node_backdrop[:3]

        if self["active"]:
            # Like the theme color, but a bit lighter and greener
            self.color = [color[0] * 0.8, color[1] * 1.5, color[2] * 0.8]
        else:
            # Like the theme color, but a bit darker
            self.color = [x * 0.6 for x in color]

    def disable_other_outputs(self):
        node_tree = self.id_data
        if node_tree is None:
            return
        for node in get_output_nodes(node_tree):
            if node == self:
                continue

            if node.active:
                node.set_active(False)
                # There can only be one active output at a time, so
                # we don't need to check the others
                break
