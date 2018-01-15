We follow the Python code style (PEP 8).

The most important stuff:
* All strings are surrounded by double quotes: "text"
* classes use CamelCase (except where Blender needs special class names, e.g. operators)
* methods and functions are lowercase, words separated by underscores: update_objects()
* "private" methods/members start with a leading underscore: _internal_update()

For UI texts (buttons, tooltips, panel names) we follow the Blender guidelines:
https://wiki.blender.org/index.php/Dev:Doc/Code_Style#UI_Messages

For UI panel classes, follow this naming scheme (section "Naming"):
https://wiki.blender.org/index.php/Dev:2.8/Source/Python/UpdatingScripts

See also issue #47: ["Rename UI classes to follow Blender's naming conventions"](https://github.com/LuxCoreRender/BlendLuxCore/issues/47)
