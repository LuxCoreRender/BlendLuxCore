import bpy
from bpy.types import NodeTree
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
from ...ui import ICON_VOLUME
from ..nodeitems import Separator
from .. import LuxCoreNodeTree

from .output import LuxCoreNodeVolOutput
from .clear import LuxCoreNodeVolClear
from .homogeneous import LuxCoreNodeVolHomogeneous
from .heterogeneous import LuxCoreNodeVolHeterogeneous


class LuxCoreVolumeNodeTree(LuxCoreNodeTree, NodeTree):
    bl_idname = "luxcore_volume_nodes"
    bl_label = "LuxCore Volume Nodes"
    bl_icon = ICON_VOLUME


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
        NodeItem("LuxCoreNodeTexfBM", label="fBM"),
        NodeItem("LuxCoreNodeTexMarble", label="Marble"),
        NodeItem("LuxCoreNodeTexWindy", label="Windy"),
        NodeItem("LuxCoreNodeTexWrinkled", label="Wrinkled"),
        NodeItem("LuxCoreNodeTexSmoke", label="Smoke Data"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_BLENDERTEXTURE", "Texture (Blender)", items=[
        NodeItem("LuxCoreNodeTexBlenderBlend", label="Blend"),
        NodeItem("LuxCoreNodeTexBlenderClouds", label="Clouds"),
        NodeItem("LuxCoreNodeTexBlenderDistortedNoise", label="Distorted Noise"),
        NodeItem("LuxCoreNodeTexBlenderMagic", label="Magic"),
        NodeItem("LuxCoreNodeTexBlenderMarble", label="Marble"),
        NodeItem("LuxCoreNodeTexBlenderMusgrave", label="Musgrave"),
        NodeItem("LuxCoreNodeTexBlenderNoise", label="Noise"),
        NodeItem("LuxCoreNodeTexBlenderStucci", label="Stucci"),
        NodeItem("LuxCoreNodeTexBlenderWood", label="Wood"),
        NodeItem("LuxCoreNodeTexBlenderVoronoi", label="Voronoi"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_UTILS", "Utils", items=[
        # Note: 2D textures make no sense for volumes
        NodeItem("LuxCoreNodeTexColorMix", label="Color Mix"),
        NodeItem("LuxCoreNodeTexMath", label="Math"),
        NodeItem("LuxCoreNodeTexInvert", label="Invert"),
        Separator(),
        NodeItem("LuxCoreNodeTexBand", label="Band"),
        NodeItem("LuxCoreNodeTexHSV", label="HSV"),
        NodeItem("LuxCoreNodeTexColorAtDepth", label="Color at depth"),
        NodeItem("LuxCoreNodeTexConstfloat1", label="Constant Value"),
        NodeItem("LuxCoreNodeTexConstfloat3", label="Constant Color"),
        NodeItem("LuxCoreNodeTexIORPreset", label="IOR Preset"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_MAPPING", "Mapping", items=[
        # Note: 2D mapping makes no sense for volumes
        NodeItem("LuxCoreNodeTexMapping3D", label="3D Mapping"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_LIGHT", "Light", items=[
        NodeItem("LuxCoreNodeTexLampSpectrum", label="Lamp Spectrum"),
        NodeItem("LuxCoreNodeTexBlackbody", label="Lamp Blackbody Temperature"),
        NodeItem("LuxCoreNodeTexIrregularData", label="Irregular Data"),
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
