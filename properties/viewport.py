import bpy
from bpy.props import IntProperty, EnumProperty

DESC_CPU = "Usually better suited for viewport rendering than OpenCL."
DESC_OCL = (
    "Use the GPUs specified in the device panel. Note that rendering on the GPU leads to "
    "higher latency and sometimes requires kernel recompilations when editing the scene"
)


class LuxCoreViewportSettings(bpy.types.PropertyGroup):
    halt_time = IntProperty(name="Viewport Halt Time (s)", default=10, min=1,
                                     description="How long to render in the viewport."
                                                 "When this time is reached, the render is paused")

    devices = [
        ("CPU", "CPU", DESC_CPU, 0),
        ("OCL", "OpenCL", DESC_OCL, 1),
    ]
    device = EnumProperty(name="Device", items=devices, default="CPU")
