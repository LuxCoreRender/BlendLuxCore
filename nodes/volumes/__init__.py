import bpy
from bpy.types import NodeTree
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
from ...ui import ICON_VOLUME

from .output import LuxCoreNodeVolOutput
from .clear import LuxCoreNodeVolClear
from .homogeneous import LuxCoreNodeVolHomogeneous


class LuxCoreVolumeNodeTree(NodeTree):
    bl_idname = "luxcore_volume_nodes"
    bl_label = "LuxCore Volume Nodes"
    bl_icon = ICON_VOLUME

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    # TODO figure out if we even can choose the volume node tree for the user
    # TODO because materials have interior and exterior nodetree (need to open two trees)
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
        return context.space_data.tree_type == "luxcore_volume_nodes"


# Here we define the menu structure the user sees when he
# presses Shift+A in the node editor to add a new node
luxcore_node_categories_volume = [
    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_VOLUME", "Volume", items=[
        NodeItem("LuxCoreNodeVolClear", label="Clear"),
        NodeItem("LuxCoreNodeVolHomogeneous", label="Homogeneous"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_TEXTURE", "Texture", items=[
        NodeItem("LuxCoreNodeTexCheckerboard3D", label="3D Checkerboard"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_MAPPING", "Mapping", items=[
        # Note: 2D mapping and 2D textures makes no sense for volumes
        NodeItem("LuxCoreNodeTexMapping3D", label="3D Mapping"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_OUTPUT", "Output", items=[
        NodeItem("LuxCoreNodeVolOutput", label="Output"),
    ]),
]

def register():
    nodeitems_utils.register_node_categories("LUXCORE_VOLUME_TREE", luxcore_node_categories_volume)


def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_VOLUME_TREE")
