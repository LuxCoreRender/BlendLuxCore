from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from .. import icons
from ..icons import icon_manager

class LUXCORE_RENDER_PT_tools(Panel, RenderButtonsPanel):
    bl_label = "LuxCore Tools"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 999

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Buttons for Network Render and Wiki
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
        col = flow.column(align=True)
        col.operator("luxcore.start_pyluxcoretools")
        col = flow.column(align=True)
        op = col.operator("luxcore.open_website", icon=icons.URL, text="Wiki")
        op.url = "https://wiki.luxcorerender.org/BlendLuxCore_Network_Rendering"

        layout.operator("luxcore.convert_to_v23")
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

class LUXCORE_RENDER_PT_filesaver(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Filesaver"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "LUXCORE_RENDER_PT_tools"

    def draw_header(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        layout.prop(config, "use_filesaver", text="")

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.enabled = config.use_filesaver
        layout.label(text="Only write LuxCore scene to disk", icon=icons.INFO)

        col = layout.column(align=True)
        col.prop(config, "filesaver_format")
        col.prop(config, "filesaver_path")
