_needs_reload = "bpy" in locals()

import bpy
from ... import properties
from ... import utils

from . import (
    carpaint, cloth, disney, emission, frontbackopacity, glass, glossy2, glossycoating,
    glossytranslucent, matte, mattetranslucent, metal, mirror, mix, null, output, tree,
    twosided, velvet,
)
import nodeitems_utils
from . import tree
from .tree import luxcore_node_categories_material

if _needs_reload:
    import importlib

    # Caveat: module order matters (due to PointerProperty and PropertyGroup)
    modules = (
        carpaint,
        cloth,
        disney,
        emission,
        frontbackopacity,
        glass,
        glossy2,
        glossycoating,
        glossytranslucent,
        matte,
        mattetranslucent,
        metal,
        mirror,
        mix,
        null,
        output,
        tree,
        twosided,
        velvet,
        nodeitems_utils,
    )
    for module in modules:
        importlib.reload(module)

classes = (
    carpaint.LuxCoreNodeMatCarpaint,
    carpaint.LuxCoreSocketReflection,
    cloth.LuxCoreSocketRepeatU,
    cloth.LuxCoreSocketRepeatV,
    cloth.LuxCoreNodeMatCloth,
    disney.LuxCoreNodeMatDisney,
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
    emission.LuxCoreNodeMatEmission,
)

def register():
    nodeitems_utils.register_node_categories("LUXCORE_MATERIAL_TREE", luxcore_node_categories_material)

    utils.register_module("Materials", classes)

def unregister():
    utils.unregister_module("Materials", classes)
    nodeitems_utils.unregister_node_categories("LUXCORE_MATERIAL_TREE")
