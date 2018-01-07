import bpy
from bpy.types import NodeTree
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
from ...ui import ICON_TEXTURE

# Import all texture nodes just so they get registered
from .checkerboard3d import LuxCoreNodeTexCheckerboard3D
from .imagemap import LuxCoreNodeTexImagemap
from .fresnel import LuxCoreNodeTexFresnel
from .colormix import LuxCoreNodeTexColorMix
from .blenderwood import LuxCoreNodeTexBlenderWood
from .mapping2d import LuxCoreNodeTexMapping2D
from .mapping3d import LuxCoreNodeTexMapping3D
from .output import LuxCoreNodeTexOutput

# TODO: how to warn if some texture nodes are incompatible with materials/volumes
# they are used in?

class LuxCoreTextureNodeTree(NodeTree):
    bl_idname = "luxcore_texture_nodes"
    bl_label = "LuxCore Texture Nodes"
    bl_icon = ICON_TEXTURE

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    # TODO figure out if we even can choose the texture node tree for the user
    # @classmethod
    # def get_from_context(cls, context):
    #     return None, None, None

    # This block updates the preview, when socket links change
    def update(self):
        self.refresh = True

    def acknowledge_connection(self, context):
        while self.refresh:
            self.refresh = False
            break

    refresh = bpy.props.BoolProperty(name="Links Changed",
                                     default=False,
                                     update=acknowledge_connection)


class LuxCoreNodeCategoryTexture(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "luxcore_texture_nodes"


# Here we define the menu structure the user sees when he
# presses Shift+A in the node editor to add a new node.
# In general it is a good idea to put often used nodes near the top.
luxcore_node_categories_texture = [
    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_TEXTURE", "Texture", items=[
        NodeItem("LuxCoreNodeTexColorMix", label="Color Mix"),
        NodeItem("LuxCoreNodeTexImagemap", label="Imagemap"),
        NodeItem("LuxCoreNodeTexFresnel", label="Fresnel"),
        NodeItem("LuxCoreNodeTexCheckerboard3D", label="3D Checkerboard"),
        NodeItem("LuxCoreNodeTexWood", label="Wood"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_MAPPING", "Mapping", items=[
        NodeItem("LuxCoreNodeTexMapping2D", label="2D Mapping"),
        NodeItem("LuxCoreNodeTexMapping3D", label="3D Mapping"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_POINTER", "Pointer", items=[
        NodeItem("LuxCoreNodeTreePointer", label="Pointer"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_OUTPUT", "Output", items=[
        NodeItem("LuxCoreNodeTexOutput", label="Output"),
    ]),
]


def register():
    nodeitems_utils.register_node_categories("LUXCORE_TEXTURE_TREE", luxcore_node_categories_texture)


def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_TEXTURE_TREE")

