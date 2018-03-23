### Design Principles

* If a setting is wrong and will cause a warning or error to be thrown at render time, warn the user **directly in the ui** about the problem. 
  Example: Any node using 2D mapping will show a warning label if the mesh does not have a UV map. 
  The only exception are cases where it is obvious, e.g. do not show a warning if no image is selected in the imagemap node.
* When exporting a lot of data in a loop, regularly (every x loop iterations, x depends on how long an iteration takes), do the following:
  * Check if the user wants to cancel the export (using [`enging.test_break()`](https://docs.blender.org/api/2.79/bpy.types.RenderEngine.html#bpy.types.RenderEngine.test_break))
  * Show the current status of the loop ("4/23 converted"), e.g. using [`engine.update_stats()`](https://docs.blender.org/api/2.79/bpy.types.RenderEngine.html#bpy.types.RenderEngine.update_stats) or [`engine.update_progress()`](https://docs.blender.org/api/2.79/bpy.types.RenderEngine.html#bpy.types.RenderEngine.update_progress)

The [fish](https://github.com/fish-shell/fish-shell#fish---the-friendly-interactive-shell-) shell 
[design document](https://fishshell.com/docs/current/design.html) outlines some more principles that are also used in BlendLuxCore, especially the *The law of discoverability*.
