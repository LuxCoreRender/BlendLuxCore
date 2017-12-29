import bpy
from . import config, display, errorlog, halt, light, material, world
from bpy.props import PointerProperty


def init():
    light.init()
    material.init()
    world.init()

    bpy.types.Scene.luxcore = PointerProperty(type=LuxCoreScene)


class LuxCoreScene(bpy.types.PropertyGroup):
    config = PointerProperty(type=config.LuxCoreConfig)
    errorlog = PointerProperty(type=errorlog.LuxCoreErrorLog)
    halt = PointerProperty(type=halt.LuxCoreHaltConditions)
    display = PointerProperty(type=display.LuxCoreDisplaySettings)
