import bpy
from bpy.props import IntProperty, BoolProperty


class LuxCoreHaltConditions(bpy.types.PropertyGroup):
    enable = BoolProperty(name="Enable", default=False)

    use_time = BoolProperty(name="Use Time", default=False)
    time = IntProperty(name="Time (s)", default=600, min=1)

    use_samples = BoolProperty(name="Use Samples", default=False)
    samples = IntProperty(name="Samples", default=500, min=1)
