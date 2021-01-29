from bl_ui.properties_scene import SceneButtonsPanel
from bpy.types import Panel
from . import icons

class LUXCORE_PT_unit_advanced(SceneButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Advanced LuxCore Settings"
    bl_parent_id ="SCENE_PT_unit"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        if config.min_epsilon >= config.max_epsilon:
            layout.label(text="", icon=icons.WARNING)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        config = scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False       

        col = layout.column(align=True)
        col.prop(config, "min_epsilon")
        col.prop(config, "max_epsilon")

        if config.min_epsilon >= config.max_epsilon:
            col = layout.column(align=True)
            col.label(text="Min epsilon should be smaller than max epsilon!", icon=icons.WARNING)


