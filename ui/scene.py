from bl_ui.properties_scene import SceneButtonsPanel
from bpy.types import Panel
from . import bpy
from . import icons

#def compatible_panels():
#     panels = [	
#     ]
#     types = bpy.types
#     return [getattr(types, p) for p in panels if hasattr(types, p)]

class LUXCORE_SCENE_PT_scene(SceneButtonsPanel, Panel):
    bl_label = "Scene"
    COMPAT_ENGINES = {'LUXCORE'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "camera")

        col = layout.column()
        row = col.row()
        row.active = False
        row.prop(scene, "background_set", text="Background")
        if scene.background_set:
            col.label(text="Background scene not supported by LuxCore", icon=icons.WARNING)
        layout.prop(scene, "active_clip", text="Active Clip")

#def register():
#    for panel in compatible_panels():
#        panel.COMPAT_ENGINES.add("LUXCORE")
    


#def unregister():
#    for panel in compatible_panels():
#        panel.COMPAT_ENGINES.remove("LUXCORE")
