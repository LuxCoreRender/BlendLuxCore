import bpy
from . import material, config, errorlog
from bpy.props import PointerProperty


def init():
    material.init()

    bpy.types.Scene.luxcore = PointerProperty(type=LuxCoreScene)


class LuxCoreScene(bpy.types.PropertyGroup):
    config = PointerProperty(type=config.LuxCoreConfig)
    errorlog = PointerProperty(type=errorlog.LuxCoreErrorLog)