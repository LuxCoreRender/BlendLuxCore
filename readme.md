<sup> [LuxCoreRender.org](https://luxcorerender.org/) | [Forums](https://forums.luxcorerender.org/) | [Wiki](http://wiki.luxcorerender.org/LuxCoreRender_Wiki) </sup>

## BlendLuxCore

This is the new Blender integration addon for LuxCore, rewritten from scratch.
It is still in early development, so expect bugs and missing features. You can find information and updates about the ongoing development in [this thread](https://forums.luxcorerender.org/viewtopic.php?f=5&t=9).

### Important

This addon requires the very latest stable version of Blender: 2.79**a**. [Download](https://www.blender.org/download/)

Note that if you save a .blend file that was opened with this addon enabled, you will not be able to open it with older Blender versions anymore.
This is because of a bug in Blender versions prior to 2.79.
See the [Blender 2.79 release notes](https://wiki.blender.org/index.php/Dev:Ref/Release_Notes/2.79/PythonAPI#Data-block_Pointer_Properties):
> Unfortunately, this new custom property type revealed a critical bug in current code, which crashes Blender on unknown property types. This bug has been fixed in 15189baa52 for the future, but it is impossible to fix this for existing releases. 
**This means that trying to load a .blend file using new data-block custom properties will crash on any version prior to 2.79.**

So if you want to render an important scene with LuxCore, please save it as a copy.

### [Report a Bug](https://github.com/LuxCoreRender/BlendLuxCore/issues/new)

Before reporting a bug, take a look at the [reported issues](https://github.com/LuxCoreRender/BlendLuxCore/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+label%3Abug) to make sure it was not already reported.

### [Download](https://luxcorerender.org/download/)

[How to install or update](https://wiki.luxcorerender.org/BlendLuxCore_Installation)

BlendLuxCore releases are fully self-contained. 
Just [install the .zip](https://docs.blender.org/manual/en/dev/preferences/addons.html#header), enable the addon, switch to the "LuxCore" engine and you're done.

### [Example Scenes](https://luxcorerender.org/download/#ExampleScenes)

TODO: These do not contain .blend files yet.

### Features

* [x] Viewport and final render
* [x] All LuxCore materials, textures, volumes and lights
* [x] Glass dispersion
* [x] IES lighting
* [x] Shadow catcher
* [x] Light groups
* [x] Cameras (perspective, ortographic, panoramic)
* [x] Depth of field
* [x] Arbitrary clipping plane
* [x] Filesaver engine (scene export to LuxCore scn/cfg files)
* [x] Object and camera motion blur
* [x] Particles
* [x] Duplis
* [x] Hair
* [x] Tonemapping settings
* [x] Imagepipeline plugins for quick effects (bloom, vignette etc.)
* [x] Transparent film
* [x] Smoke/Fire
* [x] Pointiness
* [x] AOVs (aka render passes)
* [x] Render layers
* [x] Material preview
* [ ] Image sequences
* [ ] Saving a resumable film
* [ ] Periodic film saving
* And more...

### Great new features

The reason why we are rewriting this addon. These are features that were not available in LuxBlend:

* We are now using Blender's updated PointerProperty (with ID links) for all links (node trees, images etc.) which means that if you append or link an object from another .blend file, all required node trees, image textures and so on will be appended or linked along with it.
* Much better implementation of Blender's [RenderEngine API](https://docs.blender.org/api/2.79/bpy.types.RenderEngine.html). This means that old problems like a LuxCore session rendering in the background even if you stopped the viewport render should be gone.
* AOVs (aka render passes) are now completely integrated in Blender. No more weird image hacks.

### Developer Documentation

The [doc folder](https://github.com/LuxCoreRender/BlendLuxCore/tree/master/doc) contains the documentation.

[Description of the project structure](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/doc/project_structure.md)

To create a working BlendLuxCore that can be loaded into Blender, 
you first have to copy the LuxCore binaries into the bin folder.
See [bin/readme](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/bin/readme.md) for more details.

![Example Render](https://luxcorerender.org/wp-content/uploads/2017/12/wallpaper_lux_05_rend1b.jpg)
