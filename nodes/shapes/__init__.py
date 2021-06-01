from bpy.utils import register_class, unregister_class
from . import (
    harlequin, heightdisplacement, simplify, subdiv, vectordisplacement
)

classes = (
    harlequin.LuxCoreNodeShapeHarlequin,
    heightdisplacement.LuxCoreNodeShapeHeightDisplacement,
    simplify.LuxCoreNodeShapeSimplify,
    subdiv.LuxCoreNodeShapeSubdiv,
    vectordisplacement.LuxCoreNodeShapeVectorDisplacement,
)

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in classes:
        unregister_class(cls)
