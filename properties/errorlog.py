import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty
from bpy.types import PropertyGroup


class LuxCoreError(PropertyGroup):
    message = StringProperty()
    count = IntProperty(default=1)


class LuxCoreWarning(PropertyGroup):
    message = StringProperty()
    count = IntProperty(default=1)


class LuxCoreErrorLog(PropertyGroup):
    """
    Errors here are serious exceptions that caused the render to abort

    Warnings include everything that failed where the user might want to fix it,
    report: missing textures, IES files, materials, node trees etc.
    But not every small export warning that can happen in normal Blender scenes,
    do not report: object without mesh data (aka Empty) or mesh without faces (e.g. curves used in modifiers)
    """
    errors = CollectionProperty(type=LuxCoreError)
    warnings = CollectionProperty(type=LuxCoreWarning)

    def add_error(self, message):
        self._add("ERROR:", self.errors, message)

    def add_warning(self, message):
        self._add("WARNING:", self.warnings, message)

    def clear(self):
        self.errors.clear()
        self.warnings.clear()

    def _add(self, prefix, collection, message):
        for elem in collection:
            if elem.message == message:
                elem.count += 1
                # print("Error or warning already logged. Abort adding to collection.")
                return

        print(prefix, message)

        try:
            new = collection.add()
            # Access message property without using the setter
            # (because it's read only for the user)
            new["message"] = str(message)
        except AttributeError:
            print("Can't log errors in _RestrictContext")
