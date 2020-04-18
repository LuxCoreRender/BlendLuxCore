import bpy
from . import ui as utils_ui


def update_ui():
    try:
        # Force the panel to update (if we don't do this, the added warnings
        # are only visible after the user moves the mouse over the error log panel)
        utils_ui.tag_region_for_redraw(bpy.context, "PROPERTIES", "WINDOW")
    except AttributeError:
        # print("Can't tag errorlog for redraw in _RestrictContext")
        pass


class LuxCoreError:
    def __init__(self, message, obj_name):
        self.message = str(message)
        self.count = 1
        self.obj_name = obj_name


class LuxCoreErrorLog:
    """
    Errors here are serious exceptions that caused the render to abort

    Warnings include everything that failed where the user might want to fix it,
    report: missing textures, IES files, materials, node trees etc.
    But not every small export warning that can happen in normal Blender scenes,
    do not report: object without mesh data (aka Empty) or mesh without faces (e.g. curves used in modifiers)
    """
    errors = []
    warnings = []

    @classmethod
    def add_error(cls, message, obj_name=""):
        cls._add("ERROR:", cls.errors, message, obj_name)

    @classmethod
    def add_warning(cls, message, obj_name=""):
        cls._add("WARNING:", cls.warnings, message, obj_name)

    @classmethod
    def clear(cls, force_ui_update=True):
        cls.errors.clear()
        cls.warnings.clear()
        update_ui()

    @classmethod
    def _add(cls, prefix, collection, message, obj_name):
        for elem in collection:
            if elem.message == message and elem.obj_name == obj_name:
                elem.count += 1
                # print("Error or warning already logged. Abort adding to collection.")
                return

        print(prefix, message)
        new = LuxCoreError(message, obj_name)
        collection.append(new)
        update_ui()
