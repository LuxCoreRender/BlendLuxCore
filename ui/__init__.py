import bpy

def compatible_panels():
     panels = [
#         # Data panels         
#         # Mesh
#         "DATA_PT_customdata",  # TODO do we really support this?
#         "DATA_PT_custom_props_mesh",
     ]
     types = bpy.types
     return [getattr(types, p) for p in panels if hasattr(types, p)]

#def register():   
#    bpy.types.RENDER_PT_context.append(draw_device)
#    bpy.types.VIEW3D_HT_header.append(draw_pause)     
#    for panel in compatible_panels():
#        panel.COMPAT_ENGINES.add("LUXCORE")
        
#def unregister():
#    bpy.types.RENDER_PT_context.append(draw_device)
#    bpy.types.VIEW3D_HT_header.append(draw_pause)
#    for panel in compatible_panels():
#        panel.COMPAT_ENGINES.remove("LUXCORE")

