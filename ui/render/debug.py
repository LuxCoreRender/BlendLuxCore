from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel


class LUXCORE_RENDER_PT_debug_settings(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore DEBUG Settings"
    bl_options = {'DEFAULT_CLOSED'}    
    bl_order = 998

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE" and context.scene.luxcore.debug.show

    def draw_header(self, context):
        self.layout.label(text="", icon="CONSOLE")

    def draw(self, context):
        layout = self.layout
        debug = context.scene.luxcore.debug

        layout.operator("luxcore.toggle_debug_options", text="Hide and Disable Debug Options")
        layout.prop(debug, "enabled")

        col = layout.column()
        col.active = debug.enabled
        col.prop(debug, "use_opencl_cpu")
        col.prop(debug, "print_properties")
