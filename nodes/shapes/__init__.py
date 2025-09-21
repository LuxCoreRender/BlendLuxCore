from . import harlequin, heightdisplacement, simplify, subdiv, vectordisplacement
from ... import utils

classes = (
    harlequin.LuxCoreNodeShapeHarlequin,
    heightdisplacement.LuxCoreNodeShapeHeightDisplacement,
    simplify.LuxCoreNodeShapeSimplify,
    subdiv.LuxCoreNodeShapeSubdiv,
    vectordisplacement.LuxCoreNodeShapeVectorDisplacement,
)

def register():
    utils.register_module("Shapes", classes)

def unregister():
    utils.unregister_module("Shapes", classes)
