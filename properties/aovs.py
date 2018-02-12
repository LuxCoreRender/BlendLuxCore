import bpy
from bpy.props import PointerProperty, BoolProperty
from bpy.types import PropertyGroup


# Note: currently attached to scene because we don't support render layers
class LuxCoreAOVSettings(PropertyGroup):
    depth = BoolProperty(name="Depth", default=True)
    samplecount = BoolProperty(name="Samplecount", default=False)
