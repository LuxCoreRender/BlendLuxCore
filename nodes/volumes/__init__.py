import bpy
from bpy.types import NodeTree
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
from ...ui import ICON_VOLUME
from ..output import get_active_output

from .output import LuxCoreNodeVolOutput
from .clear import LuxCoreNodeVolClear
from .homogeneous import LuxCoreNodeVolHomogeneous
from .heterogeneous import LuxCoreNodeVolHeterogeneous


class LuxCoreVolumeNodeTree(NodeTree):
    bl_idname = "luxcore_volume_nodes"
    bl_label = "LuxCore Volume Nodes"
    bl_icon = ICON_VOLUME

    # last_node_tree = None

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
    #             mat_node_tree = mat.luxcore.node_tree
    #             if mat_node_tree is None:
    #                 return cls.last_node_tree, mat, mat
    #
    #             output = get_active_output(mat_node_tree)
    #             interior = output.interior_volume
    #             exterior = output.exterior_volume
    #
    #             if interior:
    #                 cls.last_node_tree = interior
    #             if exterior:
    #                 cls.last_node_tree = exterior
    #
    #     return cls.last_node_tree, None, None

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
        NodeItem("LuxCoreNodeVolHeterogeneous", label="Heterogeneous"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_TEXTURE", "Texture", items=[
        # Note: 2D textures make no sense for volumes
        NodeItem("LuxCoreNodeTexBrick", label="Brick"),
        NodeItem("LuxCoreNodeTexCheckerboard3D", label="3D Checkerboard"),
        NodeItem("LuxCoreNodeTexBlenderBlend", label="Blend"),
        NodeItem("LuxCoreNodeTexBlenderClouds", label="Clouds"),
        NodeItem("LuxCoreNodeTexBlenderDistortedNoise", label="Distorted Noise"),
        NodeItem("LuxCoreNodeTexBlenderMagic", label="Magic"),
        NodeItem("LuxCoreNodeTexBlenderMarble", label="Marble"),
        NodeItem("LuxCoreNodeTexBlenderMusgrave", label="Musgrave"),
        NodeItem("LuxCoreNodeTexBlenderStucci", label="Stucci"),
        NodeItem("LuxCoreNodeTexBlenderWood", label="Wood"),
        NodeItem("LuxCoreNodeTexBlenderVoronoi", label="Voronoi"),
        NodeItem("LuxCoreNodeTexWrinkled", label="Wrinkled"),
        NodeItem("LuxCoreNodeTexSmoke", label="Smoke Data"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_UTILS", "Utils", items=[
        # Note: 2D textures make no sense for volumes
        NodeItem("LuxCoreNodeTexColorMix", label="Color Mix"),
        NodeItem("LuxCoreNodeTexMath", label="Math"),
        NodeItem("LuxCoreNodeTexHSV", label="HSV"),
        NodeItem("LuxCoreNodeTexColorAtDepth", label="Color at depth"),
        NodeItem("LuxCoreNodeTexConstfloat1", label="Constant Value"),
        NodeItem("LuxCoreNodeTexConstfloat3", label="Constant Color"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_MAPPING", "Mapping", items=[
        # Note: 2D mapping makes no sense for volumes
        NodeItem("LuxCoreNodeTexMapping3D", label="3D Mapping"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_LIGHT", "Light", items=[
        NodeItem("LuxCoreNodeTexLampSpectrum", label="Lamp Spectrum"),
        NodeItem("LuxCoreNodeTexBlackbody", label="Lamp Blackbody Temperature"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_POINTER", "Pointer", items=[
        NodeItem("LuxCoreNodeTreePointer", label="Pointer"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_OUTPUT", "Output", items=[
        NodeItem("LuxCoreNodeVolOutput", label="Output"),
    ]),
]

def register():
    nodeitems_utils.register_node_categories("LUXCORE_VOLUME_TREE", luxcore_node_categories_volume)


def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_VOLUME_TREE")
