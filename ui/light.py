from bl_ui.properties_data_light import DataButtonsPanel
import bpy
from . import icons
from ..ui.icons import icon_manager
from bpy.types import Panel
from ..utils import ui as utils_ui
from cycles.ui import panel_node_draw


class LUXCORE_LIGHT_PT_context_light(DataButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Light"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.light and engine == "LUXCORE"

    def draw_image_controls(self, context):
        layout = self.layout
        light = context.light

        layout.use_property_split = True
        layout.use_property_decorate = False      
        
        col = layout.column(align=True)
        col.label(text="Image:")
        col.template_ID(light.luxcore, "image", open="image.open")
        if light.luxcore.image:
            col.prop(light.luxcore, "gamma")
        light.luxcore.image_user.draw(layout, context.scene)

    def draw(self, context):
        layout = self.layout
        light = context.light

        row = layout.row(align=True)
        row.prop(light, "type", expand=True)

        layout.prop(light.luxcore, "use_cycles_settings")

        if context.light.luxcore.use_cycles_settings:
            self.draw_cycles_settings(context)
        else:
            self.draw_luxcore_settings(context)

    def draw_cycles_settings(self, context):
        layout = self.layout
        light = context.light
        is_area_light = light.type == "AREA"
        is_portal = is_area_light and light.cycles.is_portal

        layout.use_property_decorate = False
        layout.use_property_split = True

        if is_portal:
            col = layout.column(align=True)
            col.label(text="LuxCore doesn't have portal lights,", icon=icons.INFO)
            col.label(text="use environment light cache instead")

        col = layout.column()
        col.active = not is_portal

        col.prop(light, "color")
        col.prop(light, "energy")
        col.separator()

        if light.type == "POINT":
            col.prop(light, "shadow_soft_size", text="Size")
        elif light.type == "SUN":
            col.prop(light, "angle")
        elif is_area_light:
            col.prop(light, "shape", text="Shape")
            sub = col.column(align=True)

            if light.shape in {"SQUARE", "DISK"}:
                sub.prop(light, "size")
            elif light.shape in {"RECTANGLE", "ELLIPSE"}:
                sub.prop(light, "size", text="Size X")
                sub.prop(light, "size_y", text="Y")

        # Warnings and info regarding LuxCore use
        if is_area_light and light.shape not in {"SQUARE", "RECTANGLE"}:
            layout.label(text="Unsupported shape", icon=icons.WARNING)

        if not is_portal and not light.cycles.cast_shadow:
            layout.label(text="Cast Shadow is disabled, but unsupported by LuxCore", icon=icons.WARNING)

        if light.type == "SPOT" and light.shadow_soft_size > 0:
            layout.label(text="Size (soft shadows) not supported by LuxCore spotlights", icon=icons.WARNING)

    def draw_luxcore_settings(self, context):
        layout = self.layout
        light = context.light
        is_sunlight = light.type == "SUN" and light.luxcore.light_type == "sun"

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        row = col.row()
        row.prop(light.luxcore, "color_mode", expand=True)

        if light.type == "AREA" and light.luxcore.node_tree:
            col.label(text="Light color is defined by emission node", icon=icons.INFO)
        else:
            if light.luxcore.color_mode == "rgb":
                col.prop(light.luxcore, "rgb_gain", text="Color Tint" if is_sunlight else "Color")
            elif light.luxcore.color_mode == "temperature":
                if is_sunlight:
                    col.prop(light.luxcore, "temperature", slider=True, text="Temperature Tint")
                else:
                    col.prop(light.luxcore, "temperature", slider=True)
            else:
                raise Exception("Unknown color mode")

        if is_sunlight:
            col = col.column(align=True)
            col.label(icon="INFO", text="Sun color and brightness are")
            col.label(text="influenced by the sun light rotation")

        layout.separator()
        
        col = layout.column(align=True)
        if light.type in {"POINT", "SPOT", "AREA"}:
            col.prop(light.luxcore, "light_unit")

        if light.luxcore.light_unit == "power" and light.type in {"POINT", "SPOT", "AREA"}:
            col.prop(light.luxcore, "power")
            col.prop(light.luxcore, "efficacy")
            col.prop(light.luxcore, "normalizebycolor")
            
        elif light.luxcore.light_unit == "lumen" and light.type in {"POINT", "SPOT", "AREA"}:
            col.prop(light.luxcore, "lumen")
            col.prop(light.luxcore, "normalizebycolor")
            
        elif light.luxcore.light_unit == "candela" and light.type in {"POINT", "SPOT", "AREA"}:
            col.prop(light.luxcore, "candela")
            if light.type == "AREA":
                col.prop(light.luxcore, "per_square_meter")
            col.prop(light.luxcore, "normalizebycolor")
            
        elif light.type == "SUN" and light.luxcore.light_type == "distant":
            col.prop(light.luxcore, "gain", text='Gain (Lux)')
            col.prop(light.luxcore, "exposure", slider=True)
                
        else:
            col = layout.column(align=True)
            if light.type == "SUN" and light.luxcore.light_type == "sun":
                col.prop(light.luxcore, "sun_sky_gain")
            else:
                col.prop(light.luxcore, "gain")
            col.prop(light.luxcore, "exposure", slider=True)
                
            col = col.column(align=True)
            col.prop(light.luxcore, "normalizebycolor")

        layout.separator()

        # TODO: split this stuff into separate panels for each light type?
        if light.type == "POINT":
            layout.prop(light, "shadow_soft_size", text="Radius")                        
            
            self.draw_image_controls(context)

        elif light.type == "SUN":
            layout.prop(light.luxcore, "light_type", expand=False)

            if light.luxcore.light_type == "sun":
                layout.prop(light.luxcore, "relsize")
                layout.prop(light.luxcore, "turbidity")
                world = context.scene.world
                if world and world.luxcore.light == "sky2" and world.luxcore.sun != context.object:
                    layout.operator("luxcore.attach_sun_to_sky", icon=icons.WORLD)
            elif light.luxcore.light_type == "distant":
                layout.prop(light.luxcore, "theta")
                layout.prop(light.luxcore, "normalize_distant")
            elif light.luxcore.light_type == "hemi":
                self.draw_image_controls(context)
                layout.prop(light.luxcore, "sampleupperhemisphereonly")

        elif light.type == "SPOT":
            self.draw_image_controls(context)

        elif light.type == "AREA":
            if light.luxcore.is_laser:
                col = layout.column(align=True)
                col.prop(light, "size", text="Size")
            else:
                col = layout.column(align=True)
                col.prop(light.luxcore, "visible")
                col.prop(light.luxcore, "spread_angle", slider=True)

                col = layout.column(align=True)
                col.prop(light, "shape", expand=False)
                if light.shape not in {"SQUARE", "RECTANGLE"}:
                    col.label(text="Unsupported shape", icon=icons.WARNING)

                col = layout.column(align=True)

                if light.shape in {"RECTANGLE", "ELLIPSE"}:
                    col.prop(light, "size", text="Size X")
                    col.prop(light, "size_y", text="Y")
                else:
                    col.prop(light, "size", text="Size")

            layout.prop(light.luxcore, "is_laser")

        layout.separator()
        
        col = layout.column(align=True)
        op = col.operator("luxcore.switch_space_data_context", text="Show Light Groups")
        op.target = "SCENE"
        lightgroups = context.scene.luxcore.lightgroups
        col.prop_search(light.luxcore, "lightgroup",
                        lightgroups, "custom",
                        icon=icons.LIGHTGROUP, text="")


def draw_envlight_cache_ui(layout, scene, light_or_world):
    envlight_cache = scene.luxcore.config.envlight_cache
    col = layout.column()
    col.active = envlight_cache.enabled
    col.prop(light_or_world.luxcore, "use_envlight_cache")

    if light_or_world.luxcore.use_envlight_cache and not envlight_cache.enabled:
        layout.label(text="Cache is disabled in render settings", icon=icons.INFO)
        col = layout.column(align=True)
        col.use_property_split = False
        col.prop(envlight_cache, "enabled", text="Enable cache", toggle=True)


class LUXCORE_LIGHT_PT_volume(DataButtonsPanel, Panel):
    bl_label = "Exterior Volume"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 3
    COMPAT_ENGINES = {"LUXCORE"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        if engine != "LUXCORE":
            return False

        light = context.light
        if not light or light.luxcore.use_cycles_settings:
            return False
        return True

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        utils_ui.template_node_tree(layout, context.light.luxcore, "volume", icons.NTREE_VOLUME,
                                    "LUXCORE_VOLUME_MT_light_select_volume_node_tree",
                                    "luxcore.light_show_volume_node_tree",
                                    "luxcore.light_new_volume_node_tree",
                                    "luxcore.light_unlink_volume_node_tree")


class LUXCORE_LIGHT_PT_performance(DataButtonsPanel, Panel):
    """
    Light UI Panel, shows stuff that affects the performance of the render
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Performance"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 4

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.light and engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        light = context.light

        layout.use_property_split = True
        layout.use_property_decorate = False      

        layout.prop(light.luxcore, "importance")

        if not light.luxcore.use_cycles_settings and light.type == "SUN" and light.luxcore.light_type == "hemi":
            # infinite (with image) and constantinfinte lights
            draw_envlight_cache_ui(layout, context.scene, light)


class LUXCORE_LIGHT_PT_visibility(DataButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Visibility"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 5

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        if engine != "LUXCORE":
            return False

        light = context.light
        if not light or light.luxcore.use_cycles_settings:
            return False

        # Visible for sky2, sun, infinite, constantinfinite, area
        return ((light.type == "SUN" and light.luxcore.light_type == "sun")
                or light.type == "HEMI"
                or (light.type == "AREA" and not light.luxcore.is_laser))

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        light = context.light

        layout.use_property_split = True
        layout.use_property_decorate = False      

        # These settings only work with PATH and TILEPATH, not with BIDIR
        enabled = context.scene.luxcore.config.engine == "PATH"
        
        if not enabled:
            layout.label(text="Only supported by Path engines (not by Bidir)", icon=icons.INFO)

        col = layout.column()
        col.enabled = enabled
        col.label(text="Visibility for indirect light rays:")
        col = col.column()        
        col.prop(light.luxcore, "visibility_indirect_diffuse")
        col.prop(light.luxcore, "visibility_indirect_glossy")
        
        if light.type == "SUN":
            col.prop(light.luxcore, "sun_visibility_indirect_specular")
            if light.luxcore.sun_visibility_indirect_specular:
                col.label(text="Indirect Specular rays can create unwanted fireflies", icon=icons.WARNING)
        else: 
            col.prop(light.luxcore, "visibility_indirect_specular")


class LUXCORE_LIGHT_PT_spot(DataButtonsPanel, Panel):
    bl_label = "Spot Shape"
    bl_context = "data"    
    bl_order = 2

    @classmethod
    def poll(cls, context):
        light = context.light
        return (light and light.type == 'SPOT') and context.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        light = context.light
        
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(light, "spot_size", text="Size")
        if light.luxcore.image is None:
            col.prop(light, "spot_blend", text="Blend", slider=True)
        col.prop(light, "show_cone")


class LUXCORE_LIGHT_PT_ies_light(DataButtonsPanel, Panel):
    bl_label = "IES Light"
    bl_context = "data"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 2

    @classmethod
    def poll(cls, context):
        light = context.light
        return (light and not light.luxcore.use_cycles_settings
                and light.type in {"AREA", "POINT"} and context.engine == "LUXCORE")

    def draw_header(self, context):
        layout = self.layout
        light = context.light

        col = layout.column(align=True)
        col.prop(light.luxcore.ies, "use", text="")
        col = layout.column(align=True)
        col.label(text="", icon_value=icon_manager.get_icon_id("logotype"))


    def draw(self, context):
        layout = self.layout
        light = context.light

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.enabled = light.luxcore.ies.use
        layout.prop(light.luxcore.ies, "file_type", text="IES Data", expand=False)

        if light.luxcore.ies.file_type == "TEXT":
            layout.prop(light.luxcore.ies, "file_text")
            iesfile = light.luxcore.ies.file_text
        else:
            # light.luxcore.ies.file_type == "PATH":
            layout.prop(light.luxcore.ies, "file_path")
            iesfile = light.luxcore.ies.file_path

        col = layout.column(align=True)
        col.enabled = bool(iesfile)
        col.prop(light.luxcore.ies, "flipz")
        col.prop(light.luxcore.ies, "map_width")
        col.prop(light.luxcore.ies, "map_height")


class LUXCORE_LIGHT_PT_nodes(DataButtonsPanel, Panel):
    bl_label = "Nodes"
    bl_context = "data"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 3

    @classmethod
    def poll(cls, context):
        light = context.light
        return (light and not light.luxcore.use_cycles_settings
                and light.type == "AREA" and context.engine == "LUXCORE")

    def draw(self, context):
        layout = self.layout
        light = context.light

        layout.use_property_split = True
        layout.use_property_decorate = False

        utils_ui.template_node_tree(layout, light.luxcore, "node_tree", icons.NTREE_TEXTURE,
                                    "LUXCORE_MT_texture_select_node_tree",
                                    "luxcore.tex_show_nodetree",
                                    "luxcore.tex_nodetree_new",
                                    "luxcore.texture_unlink")


class LUXCORE_LIGHT_PT_cycles_nodes(DataButtonsPanel, Panel):
    bl_label = "Nodes"
    bl_context = "data"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        if context.engine != "LUXCORE" or not context.light:
            return False
        is_portal = context.light.type == "AREA" and context.light.cycles.is_portal
        return context.light.luxcore.use_cycles_settings and not is_portal

    def draw(self, context):
        layout = self.layout

        light = context.light
        panel_node_draw(layout, light, "OUTPUT_LIGHT", "Surface")


def compatible_panels():
    panels = [
        "DATA_PT_context_light",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")
