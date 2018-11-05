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
* Viewport render: created when shading mode is set to RENDERED, destroyed when shading mode is changed to something else.
  Also destroyed and re-created when changing frame!
* Final render: created when final render is started (e.g. by F12), destroyed when the render ends 
  (when leaving the `render(scene)` function) - with one exception, see [this issue](https://github.com/LuxCoreRender/BlendLuxCore/issues/59)
* Material preview: same as final render (we can check if we are in preview mode with `self.is_preview`,
  the rest is exactly the same)

The cleanup when the RenderEngine is destroyed happens in its `__del__()` method (stopping and deleting of the running luxcore session).

### export

This module contains an Exporter class with a bunch of caches. 
It handles the conversion of Blender objects, materials etc. into 
the [LuxCore SDL](https://wiki.luxcorerender.org/LuxCore_SDL_Reference_Manual_v2.0) 
and the definition of shapes (meshes), strands etc.

It's also responsible for scene and session updates during viewport render sessions.

Note: If we have a context (i.e. `context is not None`) then we are in viewport render mode. 
If we have no context (`context is None`) then we are in final render or material preview mode.
This is not explained/commented all the time in the code because it's such a fundamental concept.
Important: It is forbidden by the Blender API to access the context during final render, so you 
should not resort to hacks like using `bpy.context` when there is no context passed into a function.

Note also that nodes are not exported here, they have their own 
export methods in their classes (in the **nodes** directory, see below).

### handlers

Contains [handlers](https://docs.blender.org/api/2.79/bpy.app.handlers.html) for some special events.
These are functions that are executed e.g. when a .blend file is loaded, when something in the scene
is changed or when Blender is closed.

### nodes

Contains everything node-related. 

  #### materials
  
  Contains the material node tree definitions, corresponding categories and all material nodes.
  
  #### textures
  
  Contains the texture node tree definitions, corresponding categories and all texture nodes.
  
  Note that texture nodes can also be created "inline" in material or volume node trees. 
  The texture node tree is made for re-usable texture setups, for example when you want to use the same
  very complex texture setup in several different material node trees. 
  In this case you can reference the texture node tree using the Pointer node.
  
  #### volumes
  
  Contains the volume node tree definitions, corresponding categories and all volume nodes.
  
### operators

Custom operators, e.g. wrappers.

### properties

All custom properties are registered and attached here.

We group them in a `luxcore` PropertyGroup for each datablock type. Some Examples:

* `bpy.types.Material.luxcore.*`
* `bpy.types.World.luxcore.*`
* `bpy.types.Camera.luxcore.*`
* `bpy.types.Scene.luxcore.*`

So if you want to access the LuxCore node tree of a material, you can get it like this:

```python
# Assuming we have an active object, get the material
material = context.object.active_material
node_tree = material.luxcore.node_tree
print("Material", material.name, "has the following node tree:", node_tree.name)
```

### release

Scripts for creating release .zip packages. For more info see [doc/release.md](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/doc/release.md)

### tests

Automated tests. See [tests/readme.md](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/tests/readme.md).

### ui

This module contains the UI drawing code for the custom properties.
The `__init__.py` file contains the list of Blender UI panels that are compatible with BlendLuxCore.

The other files contain the UI code for our custom panels.
In these panels we display the properties defined in the **properties/** folder.

### utils

Utility functions that can be used in many different places.

Some functions are grouped, e.g. node related utility functions in `utils/node.py`. It is recommended to import them like this:
```python
from .utils import node as utils_node
# Now use one of the functions
utils_node.draw_uv_info(context, layout)
```

### Files in the main directory

* .gitignore - Rules for git to ignore some file types in the project folders
* .travis.yml - Script for the automated tests, see the **tests** section above
* `__init__.py` - The entry point of the whole addon. Responsible for registering and unregistering of classes, handlers etc.
