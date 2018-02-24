import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty
from . import aovs, config, display, errorlog, halt, opencl


def init():
    bpy.types.Scene.luxcore = PointerProperty(type=LuxCoreScene)


class LuxCoreScene(bpy.types.PropertyGroup):
    config = PointerProperty(type=config.LuxCoreConfig)
    errorlog = PointerProperty(type=errorlog.LuxCoreErrorLog)
    halt = PointerProperty(type=halt.LuxCoreHaltConditions)
    display = PointerProperty(type=display.LuxCoreDisplaySettings)
    opencl = PointerProperty(type=opencl.LuxCoreOpenCLSettings)
    # Move AOVs to render layer if we ever support them
    aovs = PointerProperty(type=aovs.LuxCoreAOVSettings)
