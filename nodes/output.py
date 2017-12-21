import bpy
from bpy.props import BoolProperty
from . import LuxCoreNode
from ..bin import pyluxcore


def get_active_output(node_tree, output_type):
    assert output_type in ("LuxCoreNodeMatOutput", "LuxCoreNodeTexOutput", "LuxCoreNodeVolOutput")

    for node in node_tree.nodes:
        node_type = getattr(node, "bl_idname", None)

        if node_type == output_type and node.active:
            return node


def get_output_nodes(node_tree):
    if node_tree.bl_idname == "luxcore_material_nodes":
        output_type = "LuxCoreNodeMatOutput"
    elif node_tree.bl_idname == "luxcore_texture_nodes":
        output_type = "LuxCoreNodeTexOutput"
    elif node_tree.bl_idname == "luxcore_volume_nodes":
        output_type = "LuxCoreNodeVolOutput"
    else:
        raise NotImplementedError("Unkown node tree type %s" % node_tree.bl_idname)

    nodes = []

    for node in node_tree.nodes:
        node_type = getattr(node, "bl_idname", None)
        if node_type == output_type:
            nodes.append(node)
    return nodes


def update_active(output_node, context):
    if not output_node.active:
        # enabled -> disabled is not allowed
        # TODO: allow it, but make it toggle back to the last active output
        output_node["active"] = True
        return

    output_node.disable_other_outputs()


class LuxCoreNodeOutput(LuxCoreNode):
    """
    Output classes for material, texture and volume node trees are derived from this class.
    Only one output node should be active at any time (this class handles that).
    """
    bl_width_min = 160

    # active = BoolProperty(name="Active", default=True, update=update_active)

    def init(self, context):
        self.disable_other_outputs()

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        layout.prop(self, "active")

    def copy(self, orig_node):
        orig_node["active"] = False

    def free(self):
        if not self.active:
            # Nothing to do
            return

        node_tree = self.id_data

        for node in get_output_nodes(node_tree):
            if node == self:
                continue
            node["active"] = True
            # There can only be one active output at a time, so
            # we don't need to check the others
            break

    def export(self, props, luxcore_name):
        raise NotImplementedError("Derived classes have to override this method!")

    def disable_other_outputs(self):
        node_tree = self.id_data
        if node_tree is None:
            return
        for node in get_output_nodes(node_tree):
            if node == self:
                continue

            if node.active:
                node["active"] = False
                # There can only be one active output at a time, so
                # we don't need to check the others
                break
