from bl_ui.properties_scene import SceneButtonsPanel
from bpy.types import Panel
from ..properties.lightgroups import MAX_CUSTOM_LIGHTGROUPS
from . import icons
from .icons import icon_manager


def lightgroup_icon(enabled):
    return icons.LIGHTGROUP_ENABLED if enabled else icons.LIGHTGROUP_DISABLED


def settings_toggle_icon(enabled):
    return icons.EXPANDABLE_OPENED if enabled else icons.EXPANDABLE_CLOSED


class LUXCORE_SCENE_PT_lightgroups(SceneButtonsPanel, Panel):
    bl_label = "LuxCore Light Groups"
    COMPAT_ENGINES = {"LUXCORE"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        groups = context.scene.luxcore.lightgroups

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.operator("luxcore.create_lightgroup_nodes", icon=icons.COMPOSITOR)

        self.draw_lightgroup(layout, groups.default, -1,
                             is_default_group=True)

        for i, group in enumerate(groups.custom):
            self.draw_lightgroup(layout, group, i)

        if len(groups.custom) < MAX_CUSTOM_LIGHTGROUPS:
            layout.operator("luxcore.add_lightgroup", icon=icons.ADD)

    @staticmethod
    def draw_lightgroup(layout, group, index, is_default_group=False):
        col = layout.column(align=True)

        # Upper row (enable/disable, name, remove)
        box = col.box()
        row = box.row()
        col = row.column()
        
        col.prop(group, "show_settings",
                 icon=settings_toggle_icon(group.show_settings),
                 icon_only=True, emboss=False)
        
        col = row.column()
        col.prop(group, "enabled",
                 icon=lightgroup_icon(group.enabled),
                 icon_only=True, toggle=True)
        
        col = row.column()
        col.enabled = group.enabled
        
        # Select object linked to Lightgroup
        
        box = col.box()
        row = box.row()
        
        if not is_default_group:
            col = row.column()
            op = col.operator("luxcore.select_objects_in_lightgroup", icon=icons.OBJECT, text="")
            op.index = index

        col = row.column()
        col.enabled = group.enabled
        
        if is_default_group:
            col.label(text="All lights without a group are in the default light group.", icon=icons.INFO)
        else:
            col.prop(group, "name", text="")            

        # Can't delete the default lightgroup
        if not is_default_group:
            op = row.operator("luxcore.remove_lightgroup",
                              text="", icon=icons.CLEAR, emboss=False)
            op.index = index
        if group.show_settings:
            # Lower row (gain settings, RGB gain, temperature)
            box = col.box()
            box.enabled = group.enabled

            row = box.row()
            row.prop(group, 'gain')

            row = box.row()
            row.prop(group, 'use_rgb_gain')
            sub = row.split()
            sub.active = group.use_rgb_gain
            sub.prop(group, 'rgb_gain')

            row = box.row()
            row.prop(group, 'use_temperature', text="Temperature (K)")
            sub = row.split()
            sub.active = group.use_temperature
            sub.prop(group, 'temperature', slider=True, text="")
