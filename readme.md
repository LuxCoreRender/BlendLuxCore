<p align="center">
<h1 align="center">BlendLuxCore</h1>
</p>
<p align="center">
<b>Blender Addon for LuxCoreRender</b>
</p>


![Example Render](https://luxcorerender.org/wp-content/uploads/2025/02/dark_mode_wide.jpg)


This addon integrates the LuxCore render engine into Blender. It offers advanced features like accelerated rendering of indirect light and efficient rendering of caustics.


## Supported Blender Versions

* BlendLuxCore v2.11.x officially supports Blender versions 4.5 LTS and 5.2 LTS
* Support for other 4.X and non-LTS releases has not been tested and is not guaranteed
* Supported platforms are Windows x86_64, Linux, MacOS Intel, MacOS ARM

**Previous BlendLuxCore releases:**
* Blender 4.2 LTS is supported by BlendLuxCore v2.10.
* Blender 2.93 is supported by BlendLuxCore v2.6.
* Blender 2.83-2.92 are supported by BlendLuxCore v2.5.
* Blender 2.83 is supported by BlendLuxCore v2.4.
* Blender 2.80, 2.81 and 2.82 are supported by BlendLuxCore v2.2 and v2.3.  
* Blender 2.79 is supported by BlendLuxCore v2.0, v2.1 and v2.2.
Supported platforms are Windows, Linux, MacOS Intel

## Installation

### From latest release (recommended)

- Find the latest suitable release of BlendLuxCrore on the release page:  
https://github.com/LuxCoreRender/BlendLuxCore/releases
- From the release assets, download extension `BlendLuxCore-*.zip`
- Open Blender and follow "Install from disk" procedure (https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html)

Beforehand, you must uninstall any previous version of BlendLuxCore: look in the "Get Extensions" panel.

See also https://wiki.luxcorerender.org/BlendLuxCore_Installation for a more detailed guide.

### Building locally from source

**Note: It is recommended to build the extension using GitHub Actions in a local fork!**

Prerequisites: you need `cmake` and `blender` installed and in your `PATH`

Build extension:
- clone this repository: `git clone https://github.com/LuxCoreRender/BlendLuxCore.git`
- configure: `cmake -S BlendLuxCore -B blc-build -DCMAKE_BUILD_TYPE=Release`
- build: `cmake --build blc-build`

To create a `Latest` release, use the option `-DCMAKE_BUILD_TYPE=Latest` in the step `configure`.

The build script then places the collected zip-file in the `blc-build/out` subfolder.

Open Blender and follow "Install from disk" procedure (https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html)

Beforehand, you may want to uninstall previous version of BlendLuxCore: look in the "Get Extensions" panel.

### Installing a development setup

To facilitate the development of BlendLuxCore (and optionally LuxCore), install BlendLuxCore in conjunction with the secondary extension [BlendLuxHelper](https://github.com/LuxCoreRender/BlendLuxHelper)

See the guide on the wiki for full instructions:
https://wiki.luxcorerender.org/Developing_and_debugging_BlendLuxCore

## Important Links

**Homepage:**        **https://luxcorerender.org/**  
**Wiki:**            **https://wiki.luxcorerender.org/**  
**Forums:**          **https://forums.luxcorerender.org/**  
**Discord:**         **https://discord.com/invite/chPGsKV**  
**Gallery:**         **https://luxcorerender.org/gallery/**  
**Example Scenes:**  **https://luxcorerender.org/example-scenes/**  

**In case of questions or support, please open an issue here on GitHub, or get in touch via the Forums or our Discord server.**