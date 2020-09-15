import bpy


def compatible_panels():
   panels = [
      # Texture panels
      "TEXTURE_PT_context",
      # Used only for particles/brushes
      "TEXTURE_PT_preview",
      "TEXTURE_PT_colors",
      "TEXTURE_PT_influence",
      "TEXTURE_PT_mapping",

      "TEXTURE_PT_image",
      "TEXTURE_PT_image_settings",
      "TEXTURE_PT_image_sampling",
      "TEXTURE_PT_image_alpha",
      "TEXTURE_PT_image_mapping",
      "TEXTURE_PT_image_mapping_crop",

      "TEXTURE_PT_blend",
      "TEXTURE_PT_clouds",
      "TEXTURE_PT_distortednoise",
      "TEXTURE_PT_magic",
      "TEXTURE_PT_marble",
      "TEXTURE_PT_musgrave",
      "TEXTURE_PT_stucci",
      "TEXTURE_PT_voronoi",
      "TEXTURE_PT_wood",
      "TEXTURE_PT_custom_props",
   ]
   types = bpy.types
   return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
   for panel in compatible_panels():
      panel.COMPAT_ENGINES.add("LUXCORE")    


def unregister():
   for panel in compatible_panels():
      panel.COMPAT_ENGINES.remove("LUXCORE")
