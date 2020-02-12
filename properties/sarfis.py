import bpy
from bpy.props import StringProperty, EnumProperty
from bpy.types import PropertyGroup


class LuxCoreSarfisSettings(PropertyGroup):
    output_dir: StringProperty(name="Output Path", default="//", subtype="DIR_PATH")

    modes = [
        ("single_frame", "Single Frame", "Only render the current frame", 0),
        ("animation", "Animation", "Render all frames as set in the output properties", 1),
    ]
    mode: EnumProperty(name="Mode", default="single_frame", items=modes)
