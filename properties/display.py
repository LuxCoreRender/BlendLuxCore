import bpy
from bpy.props import IntProperty


class LuxCoreDisplaySettings(bpy.types.PropertyGroup):
    interval = IntProperty(name="Refresh Interval (s)", default=10, min=5,
                           description="Time between film refreshes, in seconds")
    viewport_halt_time = IntProperty(name="Viewport Halt Time (s)", default=10, min=1,
                                     description="How long to render in the viewport")
