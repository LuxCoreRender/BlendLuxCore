import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty
from . import (
    config, debug, denoiser, denoiser_log, display, errorlog,
    halt, lightgroups, opencl, statistics, viewport,
)


def init():
    bpy.types.Scene.luxcore = PointerProperty(type=LuxCoreScene)


class LuxCoreScene(bpy.types.PropertyGroup):
    config: PointerProperty(type=config.LuxCoreConfig)
    denoiser: PointerProperty(type=denoiser.LuxCoreDenoiser)
    denoiser_log: PointerProperty(type=denoiser_log.LuxCoreDenoiserLog)
    errorlog: PointerProperty(type=errorlog.LuxCoreErrorLog)
    halt: PointerProperty(type=halt.LuxCoreHaltConditions)
    display: PointerProperty(type=display.LuxCoreDisplaySettings)
    opencl: PointerProperty(type=opencl.LuxCoreOpenCLSettings)
    lightgroups: PointerProperty(type=lightgroups.LuxCoreLightGroupSettings)
    viewport: PointerProperty(type=viewport.LuxCoreViewportSettings)
    statistics: PointerProperty(type=statistics.LuxCoreRenderStatsCollection)
    debug: PointerProperty(type=debug.LuxCoreDebugSettings)

    # Set during render and used during export
    # TODO does this have to be an IntProperty? why not active_layer_index = -1
    # TODO having it as property sometimes causes exceptions when in _RestrictContext
    active_layer_index: IntProperty(default=-1)
