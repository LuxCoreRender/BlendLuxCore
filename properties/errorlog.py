import bpy
from bpy.types import PropertyGroup
from ..utils import ui as utils_ui


class LuxCoreError:
    def __init__(self, message, obj_name):
        self.message = str(message)
        self.count = 1
        self.obj_name = obj_name


class LuxCoreErrorLog(PropertyGroup):
    """
    Errors here are serious exceptions that caused the render to abort

    Warnings include everything that failed where the user might want to fix it,
    report: missing textures, IES files, materials, node trees etc.
    But not every small export warning that can happen in normal Blender scenes,
    do not report: object without mesh data (aka Empty) or mesh without faces (e.g. curves used in modifiers)
    """
    errors = []
    warnings = []

    def add_error(self, message, obj_name=""):
        self._add("ERROR:", self.errors, message, obj_name)

    def add_warning(self, message, obj_name=""):
        self._add("WARNING:", self.warnings, message, obj_name)

    def clear(self):
        self.errors.clear()
        self.warnings.clear()

        try:
            # Force the panel to update (if we don't do this, the added warnings
            # are only visible after the user moves the mouse over the error log panel)
            utils_ui.tag_region_for_redraw(bpy.context, "PROPERTIES", "WINDOW")
        except AttributeError:
            # print("Can't tag errorlog for redraw in _RestrictContext")
            pass

    def _add(self, prefix, collection, message, obj_name):
        for elem in collection:
            if elem.message == message:
                elem.count += 1
                # print("Error or warning already logged. Abort adding to collection.")
                return

        print(prefix, message)
        new = LuxCoreError(message, obj_name)
        collection.append(new)

        try:
            # Force the panel to update (if we don't do this, the added warnings
            # are only visible after the user moves the mouse over the error log panel)
            utils_ui.tag_region_for_redraw(bpy.context, "PROPERTIES", "WINDOW")
        except AttributeError:
            # print("Can't tag errorlog for redraw in _RestrictContext")
            pass
