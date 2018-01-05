import bpy
from bpy.props import StringProperty, CollectionProperty
from bpy.types import PropertyGroup


def read_only(string_property, value):
    print("tried to access")
    pass


class LuxCoreError(PropertyGroup):
    message = StringProperty()


class LuxCoreWarning(PropertyGroup):
    message = StringProperty()


class LuxCoreErrorLog(PropertyGroup):
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
        print(prefix, message)

        for elem in collection:
            if elem.message == message:
                print("Error or warning already logged. Abort adding to collection.")
                return

        collection.add()
        new = collection[-1]
        # Access message property without using the setter
        # (because it's read only for the user)
        new["message"] = str(message)
