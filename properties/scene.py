import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty
from . import (
    config, denoiser, denoiser_log, display, errorlog,
    halt, lightgroups, opencl, viewport,
)


def init():
    bpy.types.Scene.luxcore = PointerProperty(type=LuxCoreScene)


class LuxCoreScene(bpy.types.PropertyGroup):
    config = PointerProperty(type=config.LuxCoreConfig)
    denoiser = PointerProperty(type=denoiser.LuxCoreDenoiser)
    denoiser_log = PointerProperty(type=denoiser_log.LuxCoreDenoiserLog)
    errorlog = PointerProperty(type=errorlog.LuxCoreErrorLog)
    halt = PointerProperty(type=halt.LuxCoreHaltConditions)
    display = PointerProperty(type=display.LuxCoreDisplaySettings)
    opencl = PointerProperty(type=opencl.LuxCoreOpenCLSettings)
    lightgroups = PointerProperty(type=lightgroups.LuxCoreLightGroupSettings)
    viewport = PointerProperty(type = viewport.LuxCoreViewportSettings)

    # Set during render and used during export
    active_layer_index = IntProperty(default=-1)
