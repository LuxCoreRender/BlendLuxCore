_needs_reload = "bpy" in locals()

import bpy

from . import (
    harlequin,
    heightdisplacement,
    simplify,
    subdiv,
    vectordisplacement,
    mergeondistance,
)
from ... import utils

if _needs_reload:
    import importlib

    modules = (
        harlequin,
        heightdisplacement,
        simplify,
        subdiv,
        vectordisplacement,
        mergeondistance,
    )
    for module in modules:
        importlib.reload(module)

classes = (
    harlequin.LuxCoreNodeShapeHarlequin,
    heightdisplacement.LuxCoreNodeShapeHeightDisplacement,
    simplify.LuxCoreNodeShapeSimplify,
    subdiv.LuxCoreNodeShapeSubdiv,
    vectordisplacement.LuxCoreNodeShapeVectorDisplacement,
    mergeondistance.LuxCoreNodeShapeMergeOnDistance,
)


def register():
    utils.register_module("Shapes", classes)


def unregister():
    utils.unregister_module("Shapes", classes)
