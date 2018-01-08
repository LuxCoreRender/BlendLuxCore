First, check if your problem was already reported:
[Known Bugs](https://github.com/LuxCoreRender/BlendLuxCore/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+label%3Abug)

#### System Information

Operating system and graphics card

#### Software Version

* Blender version: (example: 2.79, see splash screen)
* LuxCore version: (see BlendLuxcore addon entry in Blender user preferences)

#### Error message from Blender console

* On Linux: start Blender from a terminal to see the error messages:
  cd /path/to/blender
  ./blender
* On Windows: open Blender > "Window" menu > "Toggle System Console"

If possible, include a traceback of the error messages.
Paste it into this code block:
```
(Example output, please delete)
Traceback (most recent call last):
  File "/home/simon/.config/blender/2.79/scripts/addons/BlendLuxCore/export/light.py", line 123, in convert
    raise NotImplementedError("Area light not implemented yet")
NotImplementedError: Area light not implemented yet
```

#### Short description of error

#### Exact steps for others to reproduce the error
Based on a (as simple as possible) attached .blend file with minimum amount of steps
