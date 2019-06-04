from os.path import basename, dirname
from bpy.types import AddonPreferences


class LuxCoreAddonPreferences(AddonPreferences):
    # Must be the addon directory name
    # (by default "BlendLuxCore", but a user/dev might change the folder name)
    # We use dirname() two times to go up one level in the file system
    bl_idname = basename(dirname(dirname(__file__)))

    # We could add properties here

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Update or downgrade:")
        row.operator("luxcore.change_version")
        # Add empty space to the right of the button
        row.label(text="")
