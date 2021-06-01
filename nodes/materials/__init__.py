from bpy.utils import register_class, unregister_class
from . import (
    carpaint, cloth, disney, emission, frontbackopacity, glass, glossy2, glossycoating,
    glossytranslucent, matte, mattetranslucent, metal, mirror, mix, null, output, tree,
    twosided, velvet,
)
import nodeitems_utils
from .tree import luxcore_node_categories_material

classes = (
    carpaint.LuxCoreNodeMatCarpaint,
    carpaint.LuxCoreSocketReflection,
    cloth.LuxCoreSocketRepeatU,
    cloth.LuxCoreSocketRepeatV,
    cloth.LuxCoreNodeMatCloth,
    disney.LuxCoreNodeMatDisney,
    emission.LuxCoreNodeMatEmission,
    frontbackopacity.LuxCoreNodeMatFrontBackOpacity,
    glass.LuxCoreSocketCauchyC,
    glass.LuxCoreNodeMatGlass,
    glossy2.LuxCoreNodeMatGlossy2,
    glossycoating.LuxCoreNodeMatGlossyCoating,
    glossytranslucent.LuxCoreNodeMatGlossyTranslucent,
    matte.LuxCoreSocketSigma,
    matte.LuxCoreNodeMatMatte,
    mattetranslucent.LuxCoreNodeMatMatteTranslucent,
    metal.LuxCoreNodeMatMetal,
    mirror.LuxCoreNodeMatMirror,
    mix.LuxCoreNodeMatMix,
    null.LuxCoreNodeMatNull,
    output.LuxCoreNodeMatOutput,
    tree.LuxCoreMaterialNodeTree,
    twosided.LuxCoreNodeMatTwoSided,
    velvet.LuxCoreNodeMatVelvet,
)

def register():
    nodeitems_utils.register_node_categories("LUXCORE_MATERIAL_TREE", luxcore_node_categories_material)

    for cls in classes:
        register_class(cls)

def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_MATERIAL_TREE")

    for cls in classes:
        unregister_class(cls)
