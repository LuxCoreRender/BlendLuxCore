import bpy
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
from ...ui import icons
from ...utils import node as utils_node
from ..nodeitems import Separator, NodeItemMultiImageImport
from ..base import LuxCoreNodeTree


class LuxCoreMaterialNodeTree(bpy.types.NodeTree, LuxCoreNodeTree):
    bl_idname = "luxcore_material_nodes"
    bl_label = "LuxCore Material Nodes"
    bl_icon = icons.NTREE_MATERIAL

    @classmethod
    def get_from_context(cls, context):
        """
        Switches the displayed node tree when user selects object/material
        """
        obj = context.active_object

        if obj and obj.type not in {"LIGHT", "CAMERA"}:
            mat = obj.active_material

            if mat:
                node_tree = mat.luxcore.node_tree

                if node_tree:
                    return node_tree, mat, mat

        return None, None, None

    # This block updates the preview, when socket links change
    def update(self):
        super().update()

        # Force viewport update of the corresponding material
        for mat in bpy.data.materials:
            if mat.luxcore.node_tree == self:
                mat.diffuse_color = mat.diffuse_color
                break

        # Update opengl materials in case the node linked to the
        # output has changed
        utils_node.update_opengl_materials(None, bpy.context)


class LuxCoreNodeCategoryMaterial(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "luxcore_material_nodes"


# Here we define the menu structure the user sees when he
# presses Shift+A in the node editor to add a new node.
# In general it is a good idea to put often used nodes near the top.
luxcore_node_categories_material = [
    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_MATERIAL", "Material", items=[
        NodeItem("LuxCoreNodeMatDisney", label="Disney"),
        NodeItem("LuxCoreNodeMatMix", label="Mix"),
        NodeItem("LuxCoreNodeMatMatte", label="Matte"),
        NodeItem("LuxCoreNodeMatMatteTranslucent", label="Matte Translucent"),
        NodeItem("LuxCoreNodeMatMetal", label="Metal"),
        NodeItem("LuxCoreNodeMatMirror", label="Mirror"),
        NodeItem("LuxCoreNodeMatGlossy2", label="Glossy"),
        NodeItem("LuxCoreNodeMatGlossyTranslucent", label="Glossy Translucent"),
        NodeItem("LuxCoreNodeMatGlossyCoating", label="Glossy Coating"),
        NodeItem("LuxCoreNodeMatGlass", label="Glass"),
        NodeItem("LuxCoreNodeMatNull", label="Null (Transparent)"),
        NodeItem("LuxCoreNodeMatCarpaint", label="Carpaint"),
        NodeItem("LuxCoreNodeMatCloth", label="Cloth"),
        NodeItem("LuxCoreNodeMatVelvet", label="Velvet"),
        NodeItem("LuxCoreNodeMatFrontBackOpacity", label="Front/Back Opacity"),
    ]),

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_VOLUME", "Volume", items=[
        NodeItem("LuxCoreNodeVolClear", label="Clear"),
        NodeItem("LuxCoreNodeVolHomogeneous", label="Homogeneous"),
        NodeItem("LuxCoreNodeVolHeterogeneous", label="Heterogeneous"),
    ]),

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_TEXTURE", "Texture", items=[
        NodeItemMultiImageImport(),
        NodeItem("LuxCoreNodeTexImagemap", label="Image"),
        Separator(),
        # Procedurals
        NodeItem("LuxCoreNodeTexBrick", label="Brick"),
        NodeItem("LuxCoreNodeTexWireframe", label="Wireframe"),
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
        NodeItem("LuxCoreNodeTexFresnel", label="Fresnel"),
    ]),

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_BLENDERTEXTURE", "Texture (Blender)", items=[
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

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_MATH", "Math", items=[
        NodeItem("LuxCoreNodeTexMath", label="Math"),
        NodeItem("LuxCoreNodeTexColorMix", label="Color Math"),
        NodeItem("LuxCoreNodeTexVectorMath", label="Vector Math"),
        NodeItem("LuxCoreNodeTexDotProduct", label="Dot Product"),
        NodeItem("LuxCoreNodeTexSplitFloat3", label="Split RGB"),
        NodeItem("LuxCoreNodeTexMakeFloat3", label="Combine RGB"),
        NodeItem("LuxCoreNodeTexRemap", label="Remap"),
    ]),

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_UTILS", "Utils", items=[
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
        NodeItem("LuxCoreNodeTexRandomPerIsland", label="Random Per Island"),
        NodeItem("LuxCoreNodeTexTimeInfo", label="Time Info"),
        NodeItem("LuxCoreNodeTexUV", label="UV Test"),
        NodeItem("LuxCoreNodeTexRandom", label="Random"),
    ]),

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_MAPPING", "Mapping", items=[
        NodeItem("LuxCoreNodeTexMapping2D", label="2D Mapping"),
        NodeItem("LuxCoreNodeTexMapping3D", label="3D Mapping"),
        NodeItem("LuxCoreNodeTexTriplanar", label="Triplanar Mapping"),
        NodeItem("LuxCoreNodeTexTriplanarBump", label="Triplanar Bump Mapping"),
        NodeItem("LuxCoreNodeTexTriplanarNormalmap", label="Triplanar Normal Mapping"),
    ]),

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_LIGHT", "Light", items=[
        NodeItem("LuxCoreNodeMatEmission", label="Light Emission"),
        Separator(),
        NodeItem("LuxCoreNodeTexLampSpectrum", label="Lamp Spectrum"),
        NodeItem("LuxCoreNodeTexBlackbody", label="Blackbody Temperature"),
        NodeItem("LuxCoreNodeTexIrregularData", label="Irregular Data"),
    ]),

LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_SHAPE", "Shape Modifiers", items=[
        NodeItem("LuxCoreNodeShapeSubdiv", label="Subdivision"),
        NodeItem("LuxCoreNodeShapeHeightDisplacement", label="Height Displacement"),
        NodeItem("LuxCoreNodeShapeVectorDisplacement", label="Vector Displacement"),
        NodeItem("LuxCoreNodeShapeSimplify", label="Simplify"),
        NodeItem("LuxCoreNodeShapeHarlequin", label="Harlequin"),
    ]),

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_POINTER", "Pointer", items=[
        NodeItem("LuxCoreNodeTreePointer", label="Pointer"),
    ]),

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_OUTPUT", "Output", items=[
        NodeItem("LuxCoreNodeMatOutput", label="Output"),
    ]),

    LuxCoreNodeCategoryMaterial("LUXCORE_MATERIAL_LAYOUT", "Layout", items=[
        NodeItem("NodeFrame", label="Frame"),
        NodeItem("NodeReroute", label="Reroute"),
    ]),
]
