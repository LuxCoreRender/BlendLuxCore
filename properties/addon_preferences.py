from bpy.types import AddonPreferences


class LuxCoreAddonPreferences(AddonPreferences):
    # Must match the addon name
    bl_idname = "BlendLuxCore"

    # We could add properties here

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label("Update or downgrade:")
        row.operator("luxcore.change_version")
        # Add empty space to the right of the button
        row.label()
