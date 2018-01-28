LuxBlend rewrite

Code Design:
- no duplicate code for still/animation/viewport
- caching for still/animation/viewport (see https://github.com/LuxCoreRender/BlendLuxCore/issues/59)
- one luxcore session during animation render, with updates (to avoid kernel compilation times), see issue 59 linked above
- make viewport render robust (no running in background unwanted)
- Only use new PointerProperty, no more saving the name as StringProperty. 
  It should be possible for the user to link or append datablocks and have all 
  required dependent datablocks linked automatically.

Features:
- find out how to use the same viewport color stuff as Cycles (and/or, if that"s not possible, code something that works... in all possible editors etc.), see https://github.com/LuxCoreRender/BlendLuxCore/issues/38
- help buttons in every Lux panel header (expand to an info text explaining the feature) - or just a link to the wiki?
  In any case, make it so it's not annoying to pro users, maybe add an option in user preferences to disable the buttons

Low priority
- Useful presets for materials (e.g. "PBR", "Glossy with Specmap")
- Mesh export: use free_mpoly option in calc_tessface operation? https://www.blender.org/api/blender_python_api_2_78_release/bpy.types.Mesh.html?highlight=calc_normals_split#bpy.types.Mesh.calc_tessface

Done/Obsolete
- fast film updates (Cython? extend LuxCoreForBlender?)
- reduced filmsize during movement and/or support for RT modes
--> Dade implemented support to directly write in glBuffer
- Texture tab behaviour similar to Cycles (Brush textures, particle textures, modifier textures)
