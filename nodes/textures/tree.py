import bpy
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
from ...ui import icons
from ..nodeitems import Separator, NodeItemMultiImageImport
from ..base import LuxCoreNodeTree


class LuxCoreTextureNodeTree(bpy.types.NodeTree, LuxCoreNodeTree):
    bl_idname = "luxcore_texture_nodes"
    bl_label = "LuxCore Texture Nodes"
    bl_icon = icons.NTREE_TEXTURE


class LuxCoreNodeCategoryTexture(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "luxcore_texture_nodes"


# Here we define the menu structure the user sees when he
# presses Shift+A in the node editor to add a new node.
# In general it is a good idea to put often used nodes near the top.
luxcore_node_categories_texture = [
    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_TEXTURE", "Texture", items=[
        NodeItemMultiImageImport(),
        NodeItem("LuxCoreNodeTexImagemap", label="Image"),
        Separator(),
        # Procedurals
        NodeItem("LuxCoreNodeTexBrick", label="Brick"),
        NodeItem("LuxCoreNodeTexDots", label="Dots"),
        NodeItem("LuxCoreNodeTexfBM", label="fBM"),
        NodeItem("LuxCoreNodeTexCheckerboard2D", label="2D Checkerboard"),
        NodeItem("LuxCoreNodeTexCheckerboard3D", label="3D Checkerboard"),
        NodeItem("LuxCoreNodeTexMarble", label="Marble"),
        # NodeItem("LuxCoreNodeTexWindy", label="Windy"),  # Same as FBM -> unnecessary
        NodeItem("LuxCoreNodeTexWrinkled", label="Wrinkled"),
        Separator(),
        NodeItem("LuxCoreNodeTexHitpoint", label="Vertex Color"),
        NodeItem("LuxCoreNodeTexSmoke", label="Smoke Data"),
        NodeItem("LuxCoreNodeTexOpenVDB", label="OpenVDB File"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_BLENDERTEXTURE", "Texture (Blender)", items=[
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

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_MATH", "Math", items=[
        NodeItem("LuxCoreNodeTexBump", label="Bump"),
        # Possibly confusing, better deactivate (only needed in very rare cases anyway)
        # NodeItem("LuxCoreNodeTexNormalmap", label="Normalmap"),
        NodeItem("LuxCoreNodeTexBand", label="Band/ColorRamp"),
        NodeItem("LuxCoreNodeTexHSV", label="HSV"),
        NodeItem("LuxCoreNodeTexBrightContrast", label="Brightness/Contrast"),
        NodeItem("LuxCoreNodeTexInvert", label="Invert"),
        Separator(),
        NodeItem("LuxCoreNodeTexConstfloat1", label="Constant Value"),
        NodeItem("LuxCoreNodeTexConstfloat3", label="Constant Color"),
        NodeItem("LuxCoreNodeTexIORPreset", label="IOR Preset"),
        Separator(),
        NodeItem("LuxCoreNodeTexHitpointInfo", label="Hitpoint Info"),
        NodeItem("LuxCoreNodeTexPointiness", label="Pointiness"),
        NodeItem("LuxCoreNodeTexObjectID", label="Object ID"),
        NodeItem("LuxCoreNodeTexTimeInfo", label="Time Info"),
        NodeItem("LuxCoreNodeTexUV", label="UV Test"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_UTILS", "Utils", items=[
        NodeItem("LuxCoreNodeTexColorMix", label="Color Math"),
        NodeItem("LuxCoreNodeTexMath", label="Math"),
        NodeItem("LuxCoreNodeTexDotProduct", label="Dot Product"),
        NodeItem("LuxCoreNodeTexSplitFloat3", label="Split RGB"),
        NodeItem("LuxCoreNodeTexMakeFloat3", label="Combine RGB"),
        NodeItem("LuxCoreNodeTexRemap", label="Remap"),
        NodeItem("LuxCoreNodeTexInvert", label="Invert"),
        Separator(),
        NodeItem("LuxCoreNodeTexBump", label="Bump"),
        # Possibly confusing, better deactivate (only needed in very rare cases anyway)
        # NodeItem("LuxCoreNodeTexNormalmap", label="Normalmap"),
        NodeItem("LuxCoreNodeTexBand", label="Band"),
        NodeItem("LuxCoreNodeTexHSV", label="HSV"),
        NodeItem("LuxCoreNodeTexBrightContrast", label="Brightness/Contrast"),
        NodeItem("LuxCoreNodeTexConstfloat1", label="Constant Value"),
        NodeItem("LuxCoreNodeTexConstfloat3", label="Constant Color"),
        NodeItem("LuxCoreNodeTexIORPreset", label="IOR Preset"),
        Separator(),
        NodeItem("LuxCoreNodeTexHitpointInfo", label="Hitpoint Info"),
        NodeItem("LuxCoreNodeTexPointiness", label="Pointiness"),
        NodeItem("LuxCoreNodeTexObjectID", label="Object ID"),
        NodeItem("LuxCoreNodeTexRandomPerIsland", label="Random Per Island"),
        NodeItem("LuxCoreNodeTexTimeInfo", label="Time Info"),
        NodeItem("LuxCoreNodeTexUV", label="UV Test"),
        NodeItem("LuxCoreNodeTexRandom", label="Random"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_MAPPING", "Mapping", items=[
        NodeItem("LuxCoreNodeTexMapping2D", label="2D Mapping"),
        NodeItem("LuxCoreNodeTexMapping3D", label="3D Mapping"),
        NodeItem("LuxCoreNodeTexTriplanar", label="Triplanar Mapping"),
        NodeItem("LuxCoreNodeTexTriplanarBump", label="Triplanar Bump Mapping"),
        NodeItem("LuxCoreNodeTexTriplanarNormalmap", label="Triplanar Normal Mapping"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_LIGHT", "Light", items=[
        NodeItem("LuxCoreNodeTexLampSpectrum", label="Lamp Spectrum"),
        NodeItem("LuxCoreNodeTexBlackbody", label="Blackbody Temperature"),
        NodeItem("LuxCoreNodeTexIrregularData", label="Irregular Data"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_POINTER", "Pointer", items=[
        NodeItem("LuxCoreNodeTreePointer", label="Pointer"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_OUTPUT", "Output", items=[
        NodeItem("LuxCoreNodeTexOutput", label="Output"),
    ]),

    LuxCoreNodeCategoryTexture("LUXCORE_TEXTURE_LAYOUT", "Layout", items=[
        NodeItem("NodeFrame", label="Frame"),
        NodeItem("NodeReroute", label="Reroute"),
    ]),
]
