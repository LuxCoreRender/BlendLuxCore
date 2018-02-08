<sup> [LuxCoreRender.org](https://luxcorerender.org/) | [Forums](https://forums.luxcorerender.org/) | [Wiki](http://wiki.luxcorerender.org/LuxCoreRender_Wiki) </sup>

This is the new Blender integration addon for LuxCore, rewritten from scratch.
It is still in early development, so expect bugs and missing features.

[Information and updates about the ongoing development](https://forums.luxcorerender.org/viewtopic.php?f=5&t=9)

```diff
- Do not use the current version of this addon for real production work!
- If you want to test it on important scenes, make a copy of the .blend file first!
- You will experience crashes and other bugs. Please report them in the bug tracker!
```

**Note:** This addon requires Blender 2.79a. You can download the release candidate [here](https://download.blender.org/release/Blender2.79/) (Choose one of the links prefixed with "blender-2.79**a-rc**")

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
* [x] Basic object export
* [x] All LuxCore materials and volumes
* [x] All LuxCore textures
* [x] Glass dispersion
* [x] Imagemap textures and texture mapping
* [x] All light types (sun, sky, point, mappoint, distant, spot, projection, infinite (HDRI environment), constantinfinite, meshlights)
* [x] IES lighting
* [x] Render settings for all engines
* [x] Cameras (perspective, ortographic, panoramic)
* [x] Depth of field
* [x] Arbitrary clipping plane
* [x] FILESAVER engine (scene export to LuxCore scn/cfg files)
* [x] Object motion blur
* [x] Camera motion blur
* [x] Particles
* [x] Duplis
* [x] Tonemapping settings
* [x] Shadow catcher
* [x] Transparent film
* [x] Smoke/Fire
* [x] Pointiness
* [ ] Image sequences
* [ ] Light groups
* [ ] AOVs
* [ ] Saving a resumable film
* [ ] Most imagepipeline plugins
* [ ] Material preview
* And more...

### Great new features

The reason why we are rewriting this addon. These are features that were not available in LuxBlend:

* We are now using Blender's updated PointerProperty (with ID links) for all links (node trees, images etc.) which means that if you append or link an object from another .blend file, all required node trees, image textures and so on will be appended or linked along with it.
* Much better implementation of Blender's [RenderEngine API](https://docs.blender.org/api/2.79/bpy.types.RenderEngine.html). This means that old problems like a LuxCore session rendering in the background even if you stopped the viewport render should be gone.

### Developer Documentation

The [doc folder](https://github.com/LuxCoreRender/BlendLuxCore/tree/master/doc) contains the documentation.

[Description of the project structure](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/doc/project_structure.md)

To create a working BlendLuxCore that can be loaded into Blender, 
you first have to copy the LuxCore binaries into the bin folder.
See [bin/readme](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/bin/readme.md) for more details.

![Example Render](https://luxcorerender.org/wp-content/uploads/2017/12/wallpaper_lux_05_rend1b.jpg)
