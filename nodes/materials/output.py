import bpy
from bpy.props import BoolProperty
from .. import LuxCoreNode
from ..sockets import LuxCoreSocketMaterial
from ...bin import pyluxcore


def get_output_nodes(node_tree):
    nodes = []

    for node in node_tree.nodes:
        node_type = getattr(node, "bl_idname", None)
        if node_type == "luxcore_material_output":
            nodes.append(node)
    return nodes


def update_active(output_node, context):
    if not output_node.active:
        # enabled -> disabled is not allowed
        output_node["active"] = True
        return

    output_node.disable_other_outputs()


class luxcore_material_output(LuxCoreNode):
    """
    This is where the export starts (if the output is active).
    Only one output node should be active at any time.
    """
    bl_label = "Output"
    bl_width_min = 160

    active = BoolProperty(name="Active", default=True, update=update_active)

    def init(self, context):
        self.inputs.new("LuxCoreSocketMaterial", "Material")

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
        self.inputs["Material"].export(props, luxcore_name)

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
