# BlendLuxCore

![Example Render](https://luxcorerender.org/wp-content/uploads/2025/02/dark_mode_wide.jpg)

This addon integrates the LuxCore render engine into Blender. It offers advanced features like accelerated rendering of indirect light and efficient rendering of caustics.

## BlendLuxCore Wheels

**This is a special, experimental version of the add-on, based on LuxCore Python wheels.**
**This version is not recommended for production use.**

## Supported Blender Versions

* Blender 4.2+ is supported by the latest version
Supported platforms are Windows, Linux, MacOS Intel, MacOS ARM

**Old BlendLuxCore releases (non-wheel):**
* Blender 2.93 is supported by BlendLuxCore v2.6.
* Blender 2.83-2.92 are supported by BlendLuxCore v2.5.
* Blender 2.83 is supported by BlendLuxCore v2.4.
* Blender 2.80, 2.81 and 2.82 are supported by BlendLuxCore v2.2 and v2.3.  
* Blender 2.79 is supported by BlendLuxCore v2.0, v2.1 and v2.2.
Supported platforms are Windows, Linux, MacOS Intel

## Installation

### From latest release (recommended)

- Find the latest suitable release of **BlendLuxCore Wheels** on the release page:  
https://github.com/LuxCoreRender/BlendLuxCore/releases  
(Caveat: do not get confused with plain BlendLuxCore!)
- Note: the release labelled "latest" is a nightly build and may be particularly unstable even compared to alpha or beta release versions!
- From the release assets, download extension `BlendLuxCore-*.zip`
- Open Blender and follow "Install from disk" procedure (https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html)

Beforehand, you may want to uninstall previous version of BlendLuxCore: look in the "Get Extensions" panel.

### Building locally from source

Prerequisites: you need `cmake` and `blender` installed and in your `PATH`

Build extension:
- clone this repository: `git clone https://github.com/LuxCoreRender/BlendLuxCore.git --branch for_blender_4.2_wheels`
- configure: `cmake -S BlendLuxCore -B blc-build -DCMAKE_BUILD_TYPE=Release`
- build: `cmake --build blc-build`

To create a `Latest` release, use the option `-DCMAKE_BUILD_TYPE=Latest` in the step `configure`.

The build script then places the collected zip-file in the `blc-build` subfolder.

Open Blender and follow "Install from disk" procedure (https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html)

Beforehand, you may want to uninstall previous version of BlendLuxCore: look in the "Get Extensions" panel.

## Links

**Homepage:**        **https://luxcorerender.org/**  
**Forums:**          **https://forums.luxcorerender.org/**  
**Wiki:**            **https://wiki.luxcorerender.org/**  
**Discord:**         **https://discord.com/invite/chPGsKV**  
**Gallery:**         **https://luxcorerender.org/gallery/**  
**Example Scenes:**  **https://luxcorerender.org/example-scenes/**
