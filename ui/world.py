import bpy
from bl_ui.properties_world import WorldButtonsPanel
from bpy.types import Panel
from cycles.ui import panel_node_draw

from . import icons
from .icons import icon_manager

from ..utils import ui as utils_ui
from .light import draw_envlight_cache_ui
from ..nodes.output import get_active_output


class LUXCORE_PT_context_world(WorldButtonsPanel, Panel):
    """
    World UI Panel
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "World Light"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.world and engine == "LUXCORE"
    
    def draw(self, context):
        self.layout.prop(context.world.luxcore, "use_cycles_settings")

        if context.world.luxcore.use_cycles_settings:
            self.draw_cycles_settings(context)
        else:
            self.draw_luxcore_settings(context)

    def draw_cycles_settings(self, context):
        layout = self.layout
        world = context.world

        if not panel_node_draw(layout, world, "OUTPUT_WORLD", "Surface"):
            layout.prop(world, "color")

    def draw_luxcore_settings(self, context):
        layout = self.layout
        world = context.world

        layout.row().prop(world.luxcore, "light", expand=True)

        layout.use_property_split = True
        layout.use_property_decorate = False       

        if world.luxcore.light != "none":
            is_sky = world.luxcore.light == "sky2"
            if (is_sky or (world.luxcore.light == "infinite" and world.luxcore.image)):
                rgb_gain_label = "Tint"
            else:
                rgb_gain_label = "Color"

            col = layout.column()
            row = col.row()
            row.prop(world.luxcore, "color_mode", expand=True)

            if world.luxcore.color_mode == "rgb":
                col.prop(world.luxcore, "rgb_gain", text=rgb_gain_label)
            elif world.luxcore.color_mode == "temperature":
                col.prop(world.luxcore, "temperature", slider=True)
            else:
                raise Exception("Unknown color mode")

            has_sun = world.luxcore.sun and world.luxcore.sun.type == "LIGHT"

            col = layout.column(align=True)
            if is_sky and has_sun and world.luxcore.use_sun_gain_for_sky:
                sun = world.luxcore.sun.data
                if sun.type == "SUN" and sun.luxcore.light_type == "sun":
                    col.prop(sun.luxcore, "sun_sky_gain")
                else:
                    col.prop(sun.luxcore, "gain")
                col.prop(world.luxcore.sun.data.luxcore, "exposure", slider=True)
            else:
                if is_sky:
                    col.prop(world.luxcore, "sun_sky_gain")
                else:
                    col.prop(world.luxcore, "gain")
                col.prop(world.luxcore, "exposure", slider=True)

            if is_sky and has_sun:
                col.prop(world.luxcore, "use_sun_gain_for_sky")

            col = layout.column(align=True)
            op = col.operator("luxcore.switch_space_data_context", text="Show Light Groups")
            op.target = "SCENE"
            lightgroups = context.scene.luxcore.lightgroups
            col.prop_search(world.luxcore, "lightgroup",
                            lightgroups, "custom",
                            icon=icons.LIGHTGROUP, text="")


class LUXCORE_WORLD_PT_sky2(WorldButtonsPanel, Panel):
    """
    Sky2 UI Panel
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Sky Settings"
    bl_parent_id = "LUXCORE_PT_context_world"
    
    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        world = context.world
        return (world and not world.luxcore.use_cycles_settings
                and engine == "LUXCORE" and world.luxcore.light == "sky2")
    
    def draw(self, context):
        layout = self.layout
        world = context.world

        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(world.luxcore, "sun")
        sun = world.luxcore.sun
        if sun:
            is_really_a_sun = sun.type == "LIGHT" and sun.data and sun.data.type == "SUN"

            if is_really_a_sun:
                layout.label(text="Using turbidity of sun light:", icon=icons.INFO)
                layout.prop(sun.data.luxcore, "turbidity")
            else:
                layout.label(text="Not a sun lamp", icon=icons.WARNING)
        else:
            layout.prop(world.luxcore, "turbidity")

        # Note: ground albedo can be used without ground color
        layout.prop(world.luxcore, "groundalbedo")
        layout.prop(world.luxcore, "ground_enable")

        if world.luxcore.ground_enable:
            layout.prop(world.luxcore, "ground_color")


class LUXCORE_WORLD_PT_infinite(WorldButtonsPanel, Panel):
    """
    Infinite UI Panel
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "HDRI Settings"
    bl_parent_id = "LUXCORE_PT_context_world"

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        world = context.world
        return (world and not world.luxcore.use_cycles_settings
                and engine == "LUXCORE" and world.luxcore.light == "infinite")

    def draw(self, context):
        layout = self.layout
        world = context.world

        layout.use_property_split = True
        layout.use_property_decorate = False       
        layout.template_ID(world.luxcore, "image", open="image.open")

        sub = layout.column(align=True)
        sub.enabled = world.luxcore.image is not None
        sub.prop(world.luxcore, "gamma")
        world.luxcore.image_user.draw(sub, context.scene)
        sub.prop(world.luxcore, "rotation")
        sub.prop(world.luxcore, "sampleupperhemisphereonly")
        sub.label(text="For free transformation use a sun light", icon=icons.INFO)
        sub.operator("luxcore.create_sun_hemi")


class LUXCORE_WORLD_PT_volume(WorldButtonsPanel, Panel):
    """
    World UI Panel, shows world volume settings
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Volume"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 3

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.world and engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        world = context.world

        layout.use_property_split = True
        layout.use_property_decorate = False       
        layout.label(text="Default Volume (used on materials without attached volume):")
        utils_ui.template_node_tree(layout, world.luxcore, "volume", icons.NTREE_VOLUME,
                                    "LUXCORE_VOLUME_MT_world_select_volume_node_tree",
                                    "luxcore.world_show_volume_node_tree",
                                    "luxcore.world_new_volume_node_tree",
                                    "luxcore.world_unlink_volume_node_tree")

        config = context.scene.luxcore.config
        if config.photongi.enabled and config.engine == "PATH" and world.luxcore.volume:
            output_node = get_active_output(world.luxcore.volume)
            if output_node and output_node.use_photongi:
                col = layout.column(align=True)
                col.label(text="PhotonGI cache enabled on world volume!", icon=icons.WARNING)
                col.label(text="Can lead to VERY long cache computation time!")


class LUXCORE_WORLD_PT_performance(WorldButtonsPanel, Panel):
    """
    World UI Panel, shows stuff that affects the performance of the render
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Performance"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 4

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.world and engine == "LUXCORE" and context.world.luxcore.light != "none"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        world = context.world

        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(world.luxcore, "importance")
        draw_envlight_cache_ui(layout, context.scene, world)
    

class LUXCORE_WORLD_PT_visibility(WorldButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Ray Visibility"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 5

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        world = context.world
        return (engine == "LUXCORE" and world and world.luxcore.light != "none"
                and not world.luxcore.use_cycles_settings)

    def draw(self, context):
        layout = self.layout
        world = context.world

        layout.use_property_split = True
        layout.use_property_decorate = False

        # These settings only work with PATH and TILEPATH, not with BIDIR
        enabled = context.scene.luxcore.config.engine == "PATH"
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.label(text="Visibility for indirect light rays:")

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

        col = flow.column()
        col.prop(world.luxcore, "visibility_indirect_diffuse")
        col = flow.column()
        col.prop(world.luxcore, "visibility_indirect_glossy")
        col = flow.column()
        col.prop(world.luxcore, "visibility_indirect_specular")

        if not enabled:
            layout.label(text="Only supported by Path engines (not by Bidir)", icon=icons.INFO)

def compatible_panels():
    panels = [
        "WORLD_PT_context_world",
        "WORLD_PT_custom_props",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")
