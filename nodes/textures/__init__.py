from bpy.utils import register_class, unregister_class
from . import (
    band, blackbody, blenderblend, blenderclouds, blenderdistortednoise, blendermagic,
    blendermarble, blendermusgrave, blendernoise, blenderstucci, blendervoronoi,
    blenderwood, bombing, brick, brightcontrast, bump, checkerboard2d, checkerboard3d,
    coloratdepth, colormix, constfloat1, constfloat3, distort, dotproduct, dots, fbm,
    fresnel, hitpoint, hitpointinfo, hsv, imagemap, invert, iorpreset, irregulardata,
    lampspectrum, makefloat3, mapping2d, mapping3d, marble, math, normalmap, objectid,
    openVDB, output, pointiness, random, random_per_island, remap, smoke, splitfloat3,
    timeinfo, tree, triplanar, triplanar_bump, triplanar_normalmap, uv, vectormath,
    windy, wireframe, wrinkled,
)
import nodeitems_utils
from .tree import luxcore_node_categories_texture

classes = (
    band.ColorRampItem,
    band.LuxCoreNodeTexBand,
    blackbody.LuxCoreNodeTexBlackbody,
    blenderblend.LuxCoreNodeTexBlenderBlend,
    blenderclouds.LuxCoreNodeTexBlenderClouds,
    blenderdistortednoise.LuxCoreNodeTexBlenderDistortedNoise,
    blendermagic.LuxCoreNodeTexBlenderMagic,
    blendermarble.LuxCoreNodeTexBlenderMarble,
    blendermusgrave.LuxCoreNodeTexBlenderMusgrave,
    blendernoise.LuxCoreNodeTexBlenderNoise,
    blenderstucci.LuxCoreNodeTexBlenderStucci,
    blendervoronoi.LuxCoreNodeTexBlenderVoronoi,
    blenderwood.LuxCoreNodeTexBlenderWood,
    bombing.LuxCoreNodeTexBombing,
    brick.LuxCoreNodeTexBrick,
    brightcontrast.LuxCoreNodeTexBrightContrast,
    bump.LuxCoreNodeTexBump,
    checkerboard2d.LuxCoreNodeTexCheckerboard2D,
    checkerboard3d.LuxCoreNodeTexCheckerboard3D,
    coloratdepth.LuxCoreNodeTexColorAtDepth,
    colormix.LuxCoreNodeTexColorMix,
    constfloat1.LuxCoreNodeTexConstfloat1,
    constfloat3.LuxCoreNodeTexConstfloat3,
    distort.LuxCoreNodeTexDistort,
    dotproduct.LuxCoreNodeTexDotProduct,
    dots.LuxCoreNodeTexDots,
    fbm.LuxCoreNodeTexfBM,
    fresnel.LuxCoreNodeTexFresnel,
    hitpoint.LuxCoreNodeTexHitpoint,
    hitpointinfo.LuxCoreNodeTexHitpointInfo,
    hsv.LuxCoreNodeTexHSV,
    imagemap.LuxCoreNodeTexImagemap,
    invert.LuxCoreNodeTexInvert,
    iorpreset.LuxCoreNodeTexIORPreset,
    irregulardata.LuxCoreNodeTexIrregularData,
    lampspectrum.LuxCoreNodeTexLampSpectrum,
    makefloat3.LuxCoreNodeTexMakeFloat3,
    mapping2d.LuxCoreNodeTexMapping2D,
    mapping3d.LuxCoreNodeTexMapping3D,
    marble.LuxCoreNodeTexMarble,
    math.LuxCoreNodeTexMath,
    normalmap.LuxCoreNodeTexNormalmap,
    objectid.LuxCoreNodeTexObjectID,
    openVDB.LuxCoreNodeTexOpenVDB,
    output.LuxCoreNodeTexOutput,
    pointiness.LuxCoreNodeTexPointiness,
    random.LuxCoreNodeTexRandom,
    random_per_island.LuxCoreNodeTexRandomPerIsland,
    remap.LuxCoreNodeTexRemap,
    smoke.LuxCoreNodeTexSmoke,
    splitfloat3.LuxCoreNodeTexSplitFloat3,
    timeinfo.LuxCoreNodeTexTimeInfo,
    tree.LuxCoreTextureNodeTree,
    triplanar.LuxCoreNodeTexTriplanar,
    triplanar_bump.LuxCoreNodeTexTriplanarBump,
    triplanar_normalmap.LuxCoreNodeTexTriplanarNormalmap,
    uv.LuxCoreNodeTexUV,
    vectormath.LuxCoreNodeTexVectorMath,
    windy.LuxCoreNodeTexWindy,
    wireframe.LuxCoreNodeTexWireframe,
    wrinkled.LuxCoreNodeTexWrinkled,
)

def register():
    nodeitems_utils.register_node_categories("LUXCORE_TEXTURE_TREE", luxcore_node_categories_texture)

    for cls in classes:
        register_class(cls)

def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_TEXTURE_TREE")

    for cls in classes:
        unregister_class(cls)
