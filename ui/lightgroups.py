from bl_ui.properties_scene import SceneButtonsPanel
from bpy.types import Panel
from ..properties.lightgroups import MAX_LIGHTGROUPS

def lightgroup_icon(enabled):
    return 'OUTLINER_OB_LAMP' if enabled else 'LAMP'


def settings_toggle_icon(enabled):
    return 'TRIA_DOWN' if enabled else 'TRIA_RIGHT'


class LUXCORE_SCENE_PT_lightgroups(SceneButtonsPanel, Panel):
    bl_label = "LuxCore Light Groups"
    COMPAT_ENGINES = {"LUXCORE"}

    def draw(self, context):
        layout = self.layout
        groups = context.scene.luxcore.lightgroups

        self.draw_lightgroup(layout, groups.default, -1,
                             is_default_group=True)

        for i, group in enumerate(groups.custom):
            self.draw_lightgroup(layout, group, i)

        if len(groups.custom) < MAX_LIGHTGROUPS:
            layout.operator("luxcore.add_lightgroup", icon="ZOOMIN")

    def draw_lightgroup(self, layout, group, index, is_default_group=False):
        col = layout.column(align=True)

        # Upper row (enable/disable, name, remove)
        box = col.box()
        row = box.row()
        row.prop(group, "show_settings",
                 icon=settings_toggle_icon(group.show_settings),
                 icon_only=True, emboss=False)
        row.prop(group, "enabled",
                 icon=lightgroup_icon(group.enabled),
                 icon_only=True, toggle=True)
        sub_row = row.row()
        sub_row.active = group.enabled
        if is_default_group:
            sub_row.label("Default Light Group")
            box.label("Contains all lights without specified light group", icon="INFO")
        else:
            sub_row.prop(group, "name", text="")

        # Can't delete the default lightgroup
        if not is_default_group:
            op = row.operator("luxcore.remove_lightgroup",
                              text="", icon="X", emboss=False)
            op.index = index

        if group.show_settings:
            # Lower row (gain settings, RGB gain, temperature)
            box = col.box()
            box.active = group.enabled

            row = box.row()
            row.prop(group, 'gain')

            row = box.row()
            row.prop(group, 'use_rgb_gain')
            sub = row.split()
            sub.active = group.use_rgb_gain
            sub.prop(group, 'rgb_gain')

            row = box.row()
            row.prop(group, 'use_temperature')
            sub = row.split()
            sub.active = group.use_temperature
            sub.prop(group, 'temperature', slider=True)
