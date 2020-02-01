from bl_ui.properties_scene import SceneButtonsPanel
from bl_ui.properties_scene import SCENE_PT_scene
from bpy.types import Panel
import bpy
from . import icons

##class LUXCORE_SCENE_PT_scene(SceneButtonsPanel, Panel):
##    bl_label = "Scene"
##    bl_order = 1
##    COMPAT_ENGINES = {'LUXCORE'}
##
##    def draw(self, context):
##        layout = self.layout
##        scene = context.scene
##
##        layout.prop(scene, "camera")
##
##        col = layout.column()
##        row = col.row()
##        row.active = False
##        row.prop(scene, "background_set", text="Background")
##        if scene.background_set:
##            col.label(text="Background scene not supported by LuxCore", icon=icons.WARNING)
##        layout.prop(scene, "active_clip", text="Active Clip")

