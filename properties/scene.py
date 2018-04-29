import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty
from . import config, denoiser, display, errorlog, halt, lightgroups, opencl


def init():
    bpy.types.Scene.luxcore = PointerProperty(type=LuxCoreScene)


class LuxCoreScene(bpy.types.PropertyGroup):
    config = PointerProperty(type=config.LuxCoreConfig)
    denoiser = PointerProperty(type=denoiser.LuxCoreDenoiser)
    errorlog = PointerProperty(type=errorlog.LuxCoreErrorLog)
    halt = PointerProperty(type=halt.LuxCoreHaltConditions)
    display = PointerProperty(type=display.LuxCoreDisplaySettings)
    opencl = PointerProperty(type=opencl.LuxCoreOpenCLSettings)
    lightgroups = PointerProperty(type=lightgroups.LuxCoreLightGroupSettings)

    # Set during render and used during export
    active_layer_index = IntProperty(default=-1)
