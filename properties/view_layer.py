import bpy
from bpy.props import PointerProperty
from . import aovs, halt

class LuxCoreViewLayer(bpy.types.PropertyGroup):
    aovs: PointerProperty(type=aovs.LuxCoreAOVSettings)
    halt: PointerProperty(type=halt.LuxCoreHaltConditions)

    @classmethod
    def register(cls):
        bpy.types.ViewLayer.luxcore = PointerProperty(
            name="LuxCore ViewLayer Settings",
            description="LuxCore ViewLayer settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.ViewLayer.luxcore
