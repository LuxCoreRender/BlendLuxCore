import bpy
from bpy.props import IntProperty, BoolProperty


class LuxCoreDisplaySettings(bpy.types.PropertyGroup):
    refresh = BoolProperty(name="Refresh Film", default=False,
                           description="Update the rendered image")
    interval = IntProperty(name="Refresh Interval (s)", default=10, min=5,
                           description="Time between film refreshes, in seconds")
    viewport_halt_time = IntProperty(name="Viewport Halt Time (s)", default=10, min=1,
                                     description="How long to render in the viewport."
                                                 "When this time is reached, the render is paused")
