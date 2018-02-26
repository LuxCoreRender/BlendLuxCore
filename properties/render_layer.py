import bpy
from bpy.props import PointerProperty
from . import aovs, halt


def init():
    bpy.types.SceneRenderLayer.luxcore = PointerProperty(type=LuxCoreRenderLayer)


class LuxCoreRenderLayer(bpy.types.PropertyGroup):
    aovs = PointerProperty(type=aovs.LuxCoreAOVSettings)
    halt = PointerProperty(type=halt.LuxCoreHaltConditions)
