_needs_reload = "bpy" in locals()

import bpy

from .. import icons
from .. import utils
from . import base, sockets, materials, shapes, textures, volumes
from .base import (TREE_TYPES, TREE_ICONS, NOISE_BASIS_ITEMS, NOISE_TYPE_ITEMS, MIN_NOISE_SIZE, COLORDEPTH_DESC)

if _needs_reload:
    import importlib
    modules = (base, sockets, materials, shapes, textures, volumes)
    for module in modules:
        importlib.reload(module)


classes = (
    base.LuxCoreNodeTreePointer,
    sockets.LuxCoreSocketMaterial,
    sockets.LuxCoreSocketVolume,
    sockets.LuxCoreSocketFresnel,
    sockets.LuxCoreSocketMatEmission,
    sockets.LuxCoreSocketBump,
    sockets.LuxCoreSocketColor,
    sockets.LuxCoreSocketFloatUnbounded,
    sockets.LuxCoreSocketFloatPositive,
    sockets.LuxCoreSocketFloat0to1,
    sockets.LuxCoreSocketFloat0to2,
    sockets.LuxCoreSocketBumpHeight,
    sockets.LuxCoreSocketFloatDisneySheen,
    sockets.LuxCoreSocketVector,
    sockets.LuxCoreSocketRoughness,
    sockets.LuxCoreSocketIOR,
    sockets.LuxCoreSocketFilmThickness,
    sockets.LuxCoreSocketFilmIOR,
    sockets.LuxCoreSocketVolumeAsymmetry,
    sockets.LuxCoreSocketMapping2D,
    sockets.LuxCoreSocketMapping3D,
    sockets.LuxCoreSocketShape,
)

submodules = (materials, shapes, textures, volumes)

def register():
    utils.register_module("Nodes", classes, submodules)

def unregister():
    utils.unregister_module("Nodes", classes, submodules)
