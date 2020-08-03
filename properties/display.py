import bpy
from bpy.props import IntProperty, BoolProperty


class LuxCoreDisplaySettings(bpy.types.PropertyGroup):
    refresh = False
    paused = False
    stop_requested = False

    interval: IntProperty(name="Refresh Interval (s)", default=10, min=5,
                           description="Time between film refreshes, in seconds")

    show_converged: BoolProperty(name="Highlight Converged Tiles", default=True,
                                  description="Mark tiles that are no longer rendered with green outline")
    show_notconverged: BoolProperty(name="Highlight Unconverged Tiles", default=False,
                                     description="Mark tiles that are still rendered with red outline")
    show_pending: BoolProperty(name="Highlight Pending Tiles", default=True,
                                description="Mark tiles that are currently being worked on with yellow outline")
    show_passcounts: BoolProperty(name="Show Passes per Tile", default=True,
                                   description="Display how many passes were already done per tile")
