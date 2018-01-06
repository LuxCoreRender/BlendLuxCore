<sup> [LuxCoreRender.org](https://luxcorerender.org/) | [Forums](https://forums.luxcorerender.org/) | [Wiki](http://wiki.luxcorerender.org/LuxCoreRender_Wiki) </sup>

This is the new Blender integration addon for LuxCore, rewritten from scratch.
It is still in early development, so expect bugs and missing features.

[Information and updates about the ongoing development](https://forums.luxcorerender.org/viewtopic.php?f=5&t=9)

```diff
- Do not use the current version of this addon for real production work!
- If you want to test it on important scenes, make a copy of the .blend file first!
- You will experience crashes and other bugs. Please report them in the bug tracker!
```

### [Report a Bug](https://github.com/LuxCoreRender/BlendLuxCore/issues/new)

### [Download](https://luxcorerender.org/download/)

BlendLuxCore releases are fully self-contained. 
Just [install the .zip](https://docs.blender.org/manual/en/dev/preferences/addons.html#header), enable the addon, switch to the "LuxCore" engine and you're done.

### Working Features

* Viewport and final render
* Basic object export
* Most materials and volumes
* Glass dispersion
* Imagemap textures and texture mapping
* All light types (sun, sky, point, mappoint, distant, spot, projection, infinite (HDRI environment), constantinfinite, meshlights)
* IES lighting
* Render settings for all engines
* Cameras (perspective, ortographic, panoramic)

### Missing Features

* Particles
* Duplis
* Some materials
* Almost all textures
* Light groups
* AOVs
* Tonemapping settings
* FILESAVER engine (scene export to LuxCore scn/cfg files)
* Motion blur
* Smoke/Fire
* Depth of field
* Arbitrary clipping plane
* And more...

### Great new features

The reason why we are rewriting this addon. This are features that were not available in LuxBlend:

* We are now using Blender's updated PointerProperty (with ID links) for all links (node trees, images etc.) which means that if you append or link an object from another .blend file, all required node trees, image textures and so on will be appended or linked along with it.
* Much better implementation of Blender's [RenderEngine API](https://docs.blender.org/api/2.79/bpy.types.RenderEngine.html). This means that old problems like a LuxCore session rendering in the background even if you stopped the viewport render should be gone.

### Known Bugs

* [BlendLuxCore Bugs](https://github.com/LuxCoreRender/BlendLuxCore/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+label%3Abug)
* [Blender Bugs](https://github.com/LuxCoreRender/BlendLuxCore/issues?q=is%3Aissue+is%3Aopen+label%3A%22blender+bug%22)

### Developer Documentation

The doc folder contains the documentation.

[Description of the project structure](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/doc/project_structure.md)

To create a working BlendLuxCore that can be loaded into Blender, 
you first have to copy the LuxCore binaries into the bin folder.
See [bin/readme](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/bin/readme.md) for more details.
