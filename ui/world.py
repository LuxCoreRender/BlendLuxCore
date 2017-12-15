import bl_ui
import bpy
from . import ICON_VOLUMES


class LuxCoreWorldHeader(bl_ui.properties_world.WorldButtonsPanel, bpy.types.Panel):
    """
    World UI Panel
    """
    COMPAT_ENGINES = "LUXCORE"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.world and engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        world = context.world
        layout.prop(world.luxcore, "light", expand=True)

        row = layout.row()
        row.prop(world.luxcore, "rgb_gain")
        row.prop(world.luxcore, "gain")
        # TODO: id


class LuxCoreWorldSky2(bl_ui.properties_world.WorldButtonsPanel, bpy.types.Panel):
    """
    Sky2 UI Panel
    """
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "Sky Settings"

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        correct_light = context.world.luxcore.light == "sky2"
        return context.world and engine == "LUXCORE" and correct_light

    def draw(self, context):
        layout = self.layout
        world = context.world

        layout.prop(world.luxcore, "sun")
        sun_obj = world.luxcore.sun
        if sun_obj and sun_obj.data and sun_obj.data.type == "SUN":
            layout.label("Using turbidity of sun light:", icon="INFO")
            layout.prop(sun_obj.data.luxcore, "turbidity")
        else:
            layout.prop(world.luxcore, "turbidity")

        layout.prop(world.luxcore, "ground_enable")

        if world.luxcore.ground_enable:
            layout.prop(world.luxcore, "groundalbedo")
            layout.prop(world.luxcore, "ground_color")


class LuxCoreWorldInfinite(bl_ui.properties_world.WorldButtonsPanel, bpy.types.Panel):
    """
    Infinite UI Panel
    """
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "HDRI Settings"

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        correct_light = context.world.luxcore.light == "infinite"
        return context.world and engine == "LUXCORE" and correct_light

    def draw(self, context):
        layout = self.layout
        world = context.world

        layout.prop(world.luxcore, "image")
        layout.prop(world.luxcore, "gamma")
        layout.prop(world.luxcore, "sampleupperhemisphereonly")


class LuxCoreWorldPerformance(bl_ui.properties_world.WorldButtonsPanel, bpy.types.Panel):
    """
    World UI Panel, shows stuff that affects the performance of the render
    """
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "Performance"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.world and engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        world = context.world

        layout.prop(world.luxcore, "samples")
        layout.prop(world.luxcore, "importance")
