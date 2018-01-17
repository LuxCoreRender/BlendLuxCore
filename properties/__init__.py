import bpy
from . import (blender_object, camera, config, display,
               errorlog, halt, light, material, particle, world)
from bpy.props import PointerProperty


def init():
    blender_object.init()
    camera.init()
    light.init()
    material.init()
    particle.init()
    world.init()

    bpy.types.Scene.luxcore = PointerProperty(type=LuxCoreScene)


class LuxCoreScene(bpy.types.PropertyGroup):
    config = PointerProperty(type=config.LuxCoreConfig)
    errorlog = PointerProperty(type=errorlog.LuxCoreErrorLog)
    halt = PointerProperty(type=halt.LuxCoreHaltConditions)
    display = PointerProperty(type=display.LuxCoreDisplaySettings)
