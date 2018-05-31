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

    show_converged = BoolProperty(name="Highlight Converged Tiles", default=True,
                                  description="Mark tiles that are no longer rendered with green outline")
    show_notconverged = BoolProperty(name="Highlight Unconverged Tiles", default=False,
                                     description="Mark tiles that are still rendered with red outline")
    show_passcounts = BoolProperty(name="Show Passes Per Tile", default=True,
                                   description="Display how many passes were already done per tile")
