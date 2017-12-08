import bpy
from . import material

def compatible_panels():
    panels = [
        "RENDER_PT_render",
        "RENDER_PT_output",
        "RENDER_PT_encoding",
        "RENDER_PT_dimensions",
        "RENDER_PT_stamp",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")