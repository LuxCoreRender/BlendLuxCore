import bl_ui
from bl_ui.properties_world import WorldButtonsPanel
import bpy
from bpy.types import Panel
from . import ICON_VOLUME


class LuxCoreWorldHeader(WorldButtonsPanel, Panel):
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

        if world.luxcore.light != "none":
            split = layout.split(percentage=0.33)
            split.prop(world.luxcore, "rgb_gain", text="")
            split.prop(world.luxcore, "gain")
            # TODO: id


class LuxCoreWorldSky2(WorldButtonsPanel, Panel):
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

        # Note: ground albedo can be used without ground color
        layout.prop(world.luxcore, "groundalbedo")
        layout.prop(world.luxcore, "ground_enable")

        if world.luxcore.ground_enable:
            layout.prop(world.luxcore, "ground_color")


class LuxCoreWorldInfinite(WorldButtonsPanel, Panel):
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

        layout.template_ID(world.luxcore, "image", open="image.open")

        sub = layout.column()
        sub.enabled = world.luxcore.image is not None
        sub.prop(world.luxcore, "gamma")
        sub.prop(world.luxcore, "rotation")
        sub.label("For free transformation use a hemi lamp", icon="INFO")
        sub.prop(world.luxcore, "sampleupperhemisphereonly")


class LuxCoreWorldPerformance(WorldButtonsPanel, Panel):
    """
    World UI Panel, shows stuff that affects the performance of the render
    """
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "Performance"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return context.world and engine == "LUXCORE" and context.world.luxcore.light != "none"

    def draw(self, context):
        layout = self.layout
        world = context.world

        layout.prop(world.luxcore, "samples")
        layout.prop(world.luxcore, "importance")
