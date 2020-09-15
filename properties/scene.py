import bpy
from bpy.props import PointerProperty, IntProperty
from . import (
    config, debug, denoiser, display, halt, lightgroups, devices, statistics, viewport,
)


#def init():
#    bpy.types.Scene.luxcore = PointerProperty(type=LuxCoreScene)


class LuxCoreScene(bpy.types.PropertyGroup):
    config: PointerProperty(type=config.LuxCoreConfig)
    denoiser: PointerProperty(type=denoiser.LuxCoreDenoiser)
    halt: PointerProperty(type=halt.LuxCoreHaltConditions)
    display: PointerProperty(type=display.LuxCoreDisplaySettings)
    devices: PointerProperty(type=devices.LuxCoreDeviceSettings)
    lightgroups: PointerProperty(type=lightgroups.LuxCoreLightGroupSettings)
    viewport: PointerProperty(type=viewport.LuxCoreViewportSettings)
    statistics: PointerProperty(type=statistics.LuxCoreRenderStatsCollection)
    debug: PointerProperty(type=debug.LuxCoreDebugSettings)

    @classmethod
    def register(cls):
        bpy.types.Scene.luxcore = PointerProperty(
            name="LuxCore Scene Settings",
            description="LuxCore scene settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.luxcore
