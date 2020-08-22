import bpy
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
from ...ui import icons
from ..nodeitems import Separator
from ..base import LuxCoreNodeTree


class LuxCoreVolumeNodeTree(bpy.types.NodeTree, LuxCoreNodeTree):
    bl_idname = "luxcore_volume_nodes"
    bl_label = "LuxCore Volume Nodes"
    bl_icon = icons.NTREE_VOLUME


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
        NodeItem("LuxCoreNodeTexOpenVDB", label="OpenVDB File"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_BLENDERTEXTURE", "Texture (Blender)", items=[
        NodeItem("LuxCoreNodeTexBlenderBlend", label="Blend"),
        NodeItem("LuxCoreNodeTexBlenderClouds", label="Clouds"),
        NodeItem("LuxCoreNodeTexBlenderDistortedNoise", label="Distorted Noise"),
        NodeItem("LuxCoreNodeTexBlenderMagic", label="Magic"),
        NodeItem("LuxCoreNodeTexBlenderMarble", label="Marble"),
        NodeItem("LuxCoreNodeTexBlenderMusgrave", label="Musgrave"),
        NodeItem("LuxCoreNodeTexBlenderNoise", label="Fully Random Noise"),
        NodeItem("LuxCoreNodeTexBlenderStucci", label="Stucci"),
        NodeItem("LuxCoreNodeTexBlenderWood", label="Wood"),
        NodeItem("LuxCoreNodeTexBlenderVoronoi", label="Voronoi"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_MATH", "Math", items=[
        # Note: 2D textures make no sense for volumes
        NodeItem("LuxCoreNodeTexMath", label="Math"),
        NodeItem("LuxCoreNodeTexColorMix", label="Color Math"),
        NodeItem("LuxCoreNodeTexVectorMath", label="Vector Math"),
        NodeItem("LuxCoreNodeTexDotProduct", label="Dot Product"),
        NodeItem("LuxCoreNodeTexSplitFloat3", label="Split RGB"),
        NodeItem("LuxCoreNodeTexMakeFloat3", label="Combine RGB"),
        NodeItem("LuxCoreNodeTexRemap", label="Remap"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_UTILS", "Utils", items=[
        # Note: 2D textures make no sense for volumes
        NodeItem("LuxCoreNodeTexBand", label="ColorRamp"),
        NodeItem("LuxCoreNodeTexDistort", label="Distort"),
        NodeItem("LuxCoreNodeTexHSV", label="HSV"),
        NodeItem("LuxCoreNodeTexBrightContrast", label="Brightness/Contrast"),
        NodeItem("LuxCoreNodeTexInvert", label="Invert"),
        NodeItem("LuxCoreNodeTexColorAtDepth", label="Color at depth"),
        Separator(),
        NodeItem("LuxCoreNodeTexConstfloat1", label="Constant Value"),
        NodeItem("LuxCoreNodeTexConstfloat3", label="Constant Color"),
        NodeItem("LuxCoreNodeTexIORPreset", label="IOR Preset"),
        Separator(),
        NodeItem("LuxCoreNodeTexHitpointInfo", label="Hitpoint Info"),
        NodeItem("LuxCoreNodeTexRandom", label="Random"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_MAPPING", "Mapping", items=[
        # Note: 2D mapping makes no sense for volumes
        NodeItem("LuxCoreNodeTexMapping3D", label="3D Mapping"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_LIGHT", "Light", items=[
        NodeItem("LuxCoreNodeTexLampSpectrum", label="Lamp Spectrum"),
        NodeItem("LuxCoreNodeTexBlackbody", label="Blackbody Temperature"),
        NodeItem("LuxCoreNodeTexIrregularData", label="Irregular Data"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_POINTER", "Pointer", items=[
        NodeItem("LuxCoreNodeTreePointer", label="Pointer"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_OUTPUT", "Output", items=[
        NodeItem("LuxCoreNodeVolOutput", label="Output"),
    ]),

    LuxCoreNodeCategoryVolume("LUXCORE_VOLUME_LAYOUT", "Layout", items=[
        NodeItem("NodeFrame", label="Frame"),
        NodeItem("NodeReroute", label="Reroute"),
    ]),
]
