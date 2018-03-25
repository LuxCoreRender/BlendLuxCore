import bpy
from bpy.types import PropertyGroup
from ..utils import ui as utils_ui


class LuxCoreError:
    message = ""
    count = 1


class LuxCoreCollection(list):
    """
    Mimics Blender's CollectionProperty a bit.
    If you pass a template (must be a class) you can use the add() method
    to append more instances of that template.
    """
    def __init__(self, *args, template=None):
        list.__init__(*args)
        self.template = template

    def add(self):
        assert self.template is not None
        new = self.template()
        self.append(new)
        return new


class LuxCoreErrorLog(PropertyGroup):
    """
    Errors here are serious exceptions that caused the render to abort

    Warnings include everything that failed where the user might want to fix it,
    report: missing textures, IES files, materials, node trees etc.
    But not every small export warning that can happen in normal Blender scenes,
    do not report: object without mesh data (aka Empty) or mesh without faces (e.g. curves used in modifiers)
    """
    errors = LuxCoreCollection(LuxCoreError)
    warnings = LuxCoreCollection(LuxCoreError)

    def add_error(self, message):
        self._add("ERROR:", self.errors, message)

    def add_warning(self, message):
        self._add("WARNING:", self.warnings, message)

    def clear(self):
        self.errors.clear()
        self.warnings.clear()

        try:
            # Force the panel to update (if we don't do this, the added warnings
            # are only visible after the user moves the mouse over the error log panel)
            utils_ui.tag_region_for_redraw(bpy.context, "PROPERTIES", "WINDOW")
        except AttributeError:
            print("Can't tag errorlog for redraw in _RestrictContext")

    def _add(self, prefix, collection, message):
        for elem in collection:
            if elem.message == message:
                elem.count += 1
                # print("Error or warning already logged. Abort adding to collection.")
                return

        print(prefix, message)
        new = collection.add()
        new.message = str(message)

        try:
            # Force the panel to update (if we don't do this, the added warnings
            # are only visible after the user moves the mouse over the error log panel)
            utils_ui.tag_region_for_redraw(bpy.context, "PROPERTIES", "WINDOW")
        except AttributeError:
            print("Can't tag errorlog for redraw in _RestrictContext")
