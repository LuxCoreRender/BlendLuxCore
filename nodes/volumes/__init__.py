import bpy
from bpy.types import NodeTree
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
from ...ui import ICON_VOLUME


class LuxCoreVolumeNodeTree(NodeTree):
    bl_idname = "luxcore_volume_nodes"
    bl_label = "LuxCore Volume Nodes"
    bl_icon = ICON_VOLUME

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    # @classmethod
    # def get_from_context(cls, context):
    #     obj = context.active_object
    #
    #     if obj and obj.type not in {"LAMP", "CAMERA"}:
    #         mat = obj.active_material
    #
    #         if mat:
    #             # ID pointer
    #             node_tree = mat.luxcore.node_tree
    #
    #             if node_tree:
    #                 return node_tree, mat, mat
    #
    #     return None, None, None

    # This block updates the preview, when socket links change
    def update(self):
        self.refresh = True

    def acknowledge_connection(self, context):
        while self.refresh:
            self.refresh = False
            break

    refresh = bpy.props.BoolProperty(name='Links Changed',
                                     default=False,
                                     update=acknowledge_connection)


class LuxCoreNodeCategoryVolume(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "luxcore_material_nodes"


luxcore_node_categories_volume = [
    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_VOLUME", "Volume", items=[
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_OUTPUT", "Output", items=[
        # NodeItem("LuxCoreNodeVolOutput", label="Output"),
    ]),
]

def register():
    nodeitems_utils.register_node_categories("LUXCORE_VOLUME_TREE", luxcore_node_categories_volume)


def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_VOLUME_TREE")
