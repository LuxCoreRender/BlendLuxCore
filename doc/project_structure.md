### bin

This is where the LuxCore binary files should be put to get a working BlendLuxCore addon. 
For details, see [the Readme](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/bin/readme.md).

### doc

Documentation, tips and tricks.

### draw

Framebuffer classes for showing the rendered image on screen (viewport render and final render).

### engine

Implementation of Blenders RenderEngine API. 

It is important to know that the instances of the RenderEngine class are not persistent or a singleton.
A new instance of `LuxCoreRenderEngine` is created in these cases:
* Viewport render: created when shading mode is set to RENDERED, destroyed when shading mode is changed to something else
* Final render: created when final render is started (e.g. by F12), destroyed when the render ends 
  (when leaving the `render(scene)` function)
* Material preview: same as final render (we can check if we are in preview mode with self.is_preview, 
  the rest is exactly the same)

The cleanup when the RenderEngine is destroyed happens in its `__del__()` method (stopping and deleting of the running luxcore session).

### export

This module contains an Exporter class with a bunch of caches. 
It handles the conversion of Blender objects, materials etc. into 
the [LuxCore SDL](https://wiki.luxcorerender.org/LuxCore_SDL_Reference_Manual_v2.0) 
and the definition of shapes (meshes), strands etc.

It's also responsible for scene and session updates during viewport render sessions.

Note: If we have a context (i.e. context is not None) then we are in viewport render mode.
This is not explained/commented all the time in the code because it's such a fundamental concept.

### nodes

Contains everything node-related. 

  #### materials
  
  Contains the material node tree definitions, corresponding categories and all material nodes.
  
  #### textures
  
  Contains the texture node tree definitions, corresponding categories and all material nodes.
  
  Note that texture nodes can also be created "inline" in material or volume node trees. 
  The texture node tree is made for re-usable texture setups, for example when you want to use the same
  very complex texture setup in several different material node trees.
  
  #### volumes
  
  Contains the volume node tree definitions, corresponding categories and all material nodes.
  
### operators

Custom operators, e.g. wrappers.

### properties

All custom properties are registered and attached here.

### tests

Automated tests. See https://github.com/LuxCoreRender/BlendLuxCore/blob/master/tests/readme.md

### ui

This module contains the UI drawing code for the custom properties.

### utils

Utility functions that can be used in many different places.
