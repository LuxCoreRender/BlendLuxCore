### How to run the tests

Open terminal, cd into this folder, run
```
python3 testrunner.py /path/to/blender
```
(where `/path/to/blender` points to the blender executable)

The output will look like to this:
```
~/P/B/tests› python3 testrunner.py ~/programs/blender-2.79-linux-glibc219-x86_64/blender
found bundled python: /home/simon/programs/blender-2.79-linux-glibc219-x86_64/2.79/python
pyluxcore version: 1.7dev
Read blend: /home/simon/Projekte/BlendLuxCore/tests/./is_enabled/is_enabled.test.blend
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
LuxCoreRenderEngine del

Blender quit
~/P/B/tests›
```

This testsuite is based on the excellent article by [Ondrej Brinkel](https://anzui.de/en/blog/2015-05-21/).