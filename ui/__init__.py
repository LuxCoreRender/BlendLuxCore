import bpy
# Note: this is an include list
# We could also use an exclude list, may be shorter

def compatible_panels():
     panels = [
#         # Data panels         
#         # Mesh
#         "DATA_PT_customdata",  # TODO do we really support this?
#         "DATA_PT_custom_props_mesh",

#         # Texture panels
#         # Used only for particles/brushes
#         "TEXTURE_PT_preview",
#         "TEXTURE_PT_colors",
#         "TEXTURE_PT_influence",
#         "TEXTURE_PT_mapping",

#         # One panel per texture type
#         "TEXTURE_PT_image",
#         "TEXTURE_PT_image_mapping",
#         "TEXTURE_PT_blend",
#         "TEXTURE_PT_clouds",
#         "TEXTURE_PT_distortednoise",
#         "TEXTURE_PT_magic",
#         "TEXTURE_PT_marble",
#         "TEXTURE_PT_musgrave",
#         "TEXTURE_PT_ocean",
#         "TEXTURE_PT_pointdensity",
#         "TEXTURE_PT_pointdensity_turbulence",
#         "TEXTURE_PT_stucci",
#         "TEXTURE_PT_voronoi",
#         "TEXTURE_PT_voxeldata",
#         "TEXTURE_PT_wood",
#
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

