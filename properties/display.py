import bpy
from bpy.props import IntProperty


class LuxCoreDisplaySettings(bpy.types.PropertyGroup):
    interval = IntProperty(name="Refresh Interval (s)", default=10, min=5,
                           description="Time between film refreshes, in seconds")
