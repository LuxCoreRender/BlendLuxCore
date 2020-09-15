import bpy


def compatible_panels():
    panels = [
        "DATA_PT_context_volume",
        "DATA_PT_volume_file",
        "DATA_PT_volume_grids",
        # "DATA_PT_volume_render",  # Probably not supported by us
        "DATA_PT_volume_viewport_display",
        "DATA_PT_custom_props_volume",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
   for panel in compatible_panels():
      panel.COMPAT_ENGINES.add("LUXCORE")    


def unregister():
   for panel in compatible_panels():
      panel.COMPAT_ENGINES.remove("LUXCORE")
