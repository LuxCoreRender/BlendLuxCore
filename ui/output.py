import bpy
from . import icons
#
# # Note: The main LuxCore config UI is defined in ui/config.py
# # Each of the other render panels is also defined in their
# # own specific files in the ui/ folder.
#

def compatible_panels():
     panels = [
         "RENDER_PT_output",
         "RENDER_PT_output_views",
         "RENDER_PT_encoding",
         "RENDER_PT_encoding_video",
         "RENDER_PT_encoding_audio",         
         "RENDER_PT_dimensions",
         "RENDER_PT_stamp",
         "RENDER_PT_stamp_note",
         "RENDER_PT_stamp_burn",
         "RENDER_PT_frame_remapping",         
     ]
     types = bpy.types
     return [getattr(types, p) for p in panels if hasattr(types, p)]
     

def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")
