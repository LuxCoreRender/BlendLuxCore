from bl_ui.properties_data_light import DataButtonsPanel
from . import bpy
from . import icons
from bpy.types import Panel

# TODO: add warning/info label about gain problems (e.g. "why is my HDRI black when a sun is in the scene")
class LUXCORE_LIGHT_PT_context_light(DataButtonsPanel, Panel):
    """
    Light UI Panel
    """
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

        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(light.luxcore, "rgb_gain", text="Color")        
        layout.prop(light.luxcore, "gain")

        col = layout.column(align=True)
        op = col.operator("luxcore.switch_space_data_context", text="Show Light Groups")
        op.target = "SCENE"
        lightgroups = context.scene.luxcore.lightgroups
        col.prop_search(light.luxcore, "lightgroup",
                        lightgroups, "custom",
                        icon=icons.LIGHTGROUP, text="")
        

        layout.separator()

        # TODO: split this stuff into separate panels for each light type?
        if light.type == "POINT":
            col = layout.column(align=True)
            col.prop(light.luxcore, "power")
            col.prop(light.luxcore, "efficacy")
            
            layout.prop(light, "shadow_soft_size", text="Radius")                        
            
            self.draw_image_controls(context)

        elif light.type == "SUN":
            layout.prop(light.luxcore, "sun_type", expand=False)

            if light.luxcore.sun_type == "sun":
                layout.prop(light.luxcore, "relsize")
                layout.prop(light.luxcore, "turbidity")
                world = context.scene.world
                if world and world.luxcore.light == "sky2" and world.luxcore.sun != context.object:
                    layout.operator("luxcore.attach_sun_to_sky", icon=icons.WORLD)
            elif light.luxcore.sun_type == "distant":
                layout.prop(light.luxcore, "theta")

        elif light.type == "SPOT":
            col = layout.column(align=True)
            col.prop(light.luxcore, "power")
            col.prop(light.luxcore, "efficacy")

            self.draw_image_controls(context)

        elif light.type == "HEMI":
            self.draw_image_controls(context)
            layout.prop(light.luxcore, "sampleupperhemisphereonly")

        elif light.type == "AREA":
            col = layout.column(align=True)
            col.prop(light.luxcore, "power")
            col.prop(light.luxcore, "efficacy")

            if light.luxcore.is_laser:
                col = layout.column(align=True)
                col.prop(light, "size", text="Size")
            else:
                col = layout.column(align=True)
                if context.object:
                    col.prop(context.object.luxcore, "visible_to_camera")
                col.prop(light.luxcore, "spread_angle", slider=True)

                col = layout.column(align=True)
                col.prop(light, "shape", expand=False)

                col = layout.column(align=True)

                if light.shape == "SQUARE":
                    col.prop(light, "size", text="Size")
                else:
                    col.prop(light, "size", text="Size X")
                    col.prop(light, "size_y", text="Y")

            layout.prop(light.luxcore, "is_laser")


def draw_vismap_ui(layout, light_or_world):
    layout.prop(light_or_world.luxcore.vismap, "type")
    if light_or_world.luxcore.vismap.type == "cache":
        col = layout.column(align=True)
        col.prop(light_or_world.luxcore.vismap, "cache_map_width")
        col.prop(light_or_world.luxcore.vismap, "cache_samples")


class LUXCORE_LIGHT_PT_performance(DataButtonsPanel, Panel):
    """
    Light UI Panel, shows stuff that affects the performance of the render
    """
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Performance"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 3

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.light and engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        light = context.light

        layout.use_property_split = True
        layout.use_property_decorate = False      

        layout.prop(light.luxcore, "importance")

        if light.type == "HEMI":
            # infinite (with image) and constantinfinte lights
            draw_vismap_ui(layout, light)


class LUXCORE_LIGHT_PT_visibility(DataButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Visibility"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 4

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine

        visible = False
        if context.light:
            # Visible for sky2, sun, infinite, constantinfinite
            if context.light.type == "SUN" and context.light.luxcore.sun_type == "sun":
                visible = True
            elif context.light.type == "HEMI":
                visible = True

        return context.light and engine == "LUXCORE" and visible

    def draw(self, context):
        layout = self.layout
        light = context.light

        layout.use_property_split = True
        layout.use_property_decorate = False      

        # These settings only work with PATH and TILEPATH, not with BIDIR
        enabled = context.scene.luxcore.config.engine == "PATH"

        col = layout.column()
        col.enabled = enabled
        col.label(text="Visibility for indirect light rays:")
        col = layout.column()        
        col.prop(light.luxcore, "visibility_indirect_diffuse")
        col.prop(light.luxcore, "visibility_indirect_glossy")
        col.prop(light.luxcore, "visibility_indirect_specular")

        if not enabled:
            layout.label(text="Only supported by Path engines (not by Bidir)", icon=icons.INFO)


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
        return light and (light.type == 'AREA' or light.type == 'POINT') and context.engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        light = context.light
        
        layout.prop(light.luxcore.ies, "use", text="")

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
