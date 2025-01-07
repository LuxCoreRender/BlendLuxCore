![Watermark](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/luxcorerender-logo_orange_grey-shiny.png)

![Example](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/luxcorerender_caustics_scene.jpg)

<sup> [LuxCoreRender.org](https://luxcorerender.org/) | [Forums](https://forums.luxcorerender.org/) | [Wiki](http://wiki.luxcorerender.org/LuxCoreRender_Wiki) </sup>

## BlendLuxCore Wheels

This addon integrates the LuxCore render engine into Blender. It offers advanced features like accelerated rendering of indirect light and efficient rendering of caustics.

**This is a special, experimental version of the add-on, based on LuxCore Python wheels.** It may not be suitable for production use.

### Supported Blender Versions

* Blender 4.2 is supported for Windows, Linux, MacOS Intel, MacOS ARM

### Installation

#### From latest release (recommended)

- Find latest release of **BlendLuxCore Wheels** (https://github.com/LuxCoreRender/BlendLuxCore/releases). Caveat: do not get confused with plain BlendLuxCore.
- From the release assets, download extension `BlendLuxCore*.zip`
- Open Blender and follow "Install from disk" procedure (https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html)

Beforehand, you may want to uninstall previous version of BlendLuxCore: look in "Get Extensions" panel.

#### From last commit

Build extension:
- clone this repository: `git clone https://github.com/LuxCoreRender/BlendLuxCore.git`
- checkout branch: `git checkout for_blender_4.2_wheels`
- configure: `cmake -S BlendLuxCore -B blc-build`
- build: `cmake --build blc-build`

The extension should be in `blc-build` subfolder

Open Blender and follow "Install from disk" procedure (https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html)

Beforehand, you may want to uninstall previous version of BlendLuxCore: see in "Get Extensions" panel.

### [Gallery](https://luxcorerender.org/gallery/)

### [Download example test scenes](https://luxcorerender.org/example-scenes/)

