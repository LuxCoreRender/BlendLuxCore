import bpy
from bpy.props import StringProperty


class LuxCoreErrorLog(bpy.types.PropertyGroup):
    errors = StringProperty(name="")

    def set(self, error):
        self.errors = str(error)
