import bpy
from .. import icons
from ..icons import icon_manager
from ... import utils
from bpy.types import Panel
from bl_ui.properties_render import RENDER_PT_context
from bl_ui.properties_render import RenderButtonsPanel


def luxcore_render_draw(panel, context):
    layout = panel.layout
    scene = context.scene

    if scene.render.engine != "LUXCORE":
        return

    config = context.scene.luxcore.config

    # Device
    col_device = layout.column(align=True)
    if config.engine == "PATH":
        col_device.prop(config, "device", text="Compute device", icon = 'MEMORY')
        
        if config.device == "OCL":
            gpu_backend = utils.get_addon_preferences(context).gpu_backend
            
            if gpu_backend == "OPENCL" and not utils.is_opencl_build():
                col_device.label(text="No OpenCL support in this BlendLuxCore version", icon=icons.ERROR)
            if gpu_backend == "CUDA" and not utils.is_cuda_build():
                col_device.label(text="No CUDA support in this BlendLuxCore version", icon=icons.ERROR)
    else:
        col_device.enabled = False
        col_device.prop(config, "bidir_device", text="Device")

    # Engine
    col = layout.column(align=True)
    col.prop(config, "engine", expand=False, icon = 'OUTLINER_OB_LIGHT')

    row = layout.row()
    row.operator("luxcore.use_cycles_settings", icon_value= icon_manager.get_icon_id("link"))
    row.operator("luxcore.render_settings_helper", icon_value= icon_manager.get_icon_id("help"))

class LUXCORE_RENDER_PT_lightpaths(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Light Paths"
    bl_order = 20
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))
    
    def draw(self, context):
        pass

class LUXCORE_RENDER_PT_lightpaths_bounces(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDER_PT_lightpaths"
    bl_label = "Max Bounces"

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        if config.engine == "PATH":
            # Path options
            col.prop(config.path, "depth_total")

            def draw_bounce_prop(layout, name):
                row = layout.row(align=True)
                row.alert = getattr(config.path, name) > config.path.depth_total
                row.prop(config.path, name)

            col = layout.column(align=True)
            draw_bounce_prop(col, "depth_diffuse")
            draw_bounce_prop(col, "depth_glossy")
            draw_bounce_prop(col, "depth_specular")
        else:
            # Bidir options
            col.prop(config, "bidir_path_maxdepth")
            col.prop(config, "bidir_light_maxdepth")

class LUXCORE_RENDER_PT_add_light_tracing(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Light Tracing"
    bl_parent_id = "LUXCORE_RENDER_PT_lightpaths"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        config = context.scene.luxcore.config
        engine = context.scene.render.engine
        return config.engine == "PATH" and not config.use_tiles and engine == 'LUXCORE'

    def error(self, context):
        use_native_cpu = context.scene.luxcore.devices.use_native_cpu
        config = context.scene.luxcore.config
        return config.device == "OCL" and not use_native_cpu

    def draw_header(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        layout.prop(config.path, "hybridbackforward_enable", text="")

        if config.path.hybridbackforward_enable and self.error(context):
            layout.label(icon=icons.WARNING)

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.enabled = config.path.hybridbackforward_enable

        if config.device == "CPU":
            layout.prop(config.path, "hybridbackforward_lightpartition")
        else:
            layout.prop(config.path, "hybridbackforward_lightpartition_opencl")
        layout.prop(config.path, "hybridbackforward_glossinessthresh")

        if self.error(context):
            layout.label(text='Enable "Use CPUs" in LuxCore device settings', icon=icons.WARNING)

            col = layout.column(align=True)
            col.use_property_split = False
            col.prop(context.scene.luxcore.devices, "use_native_cpu", toggle=True, text="Fix this problem")


class LUXCORE_RENDER_PT_lightpaths_clamping(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDER_PT_lightpaths"
    bl_label = "Clamping"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header(self, context):
        layout = self.layout
        config = context.scene.luxcore.config        
        layout.prop(config.path, "use_clamping", text="")
      
    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False      
      
        layout.active = config.path.use_clamping
        layout.prop(config.path, "clamping")

        if config.path.suggested_clamping_value == -1:
            # Optimal clamp value not yet found, need to start a render first
            if config.path.use_clamping:
                # Can't compute optimal value if clamping is enabled
                layout.label(text="Render without clamping to get suggested clamp value", icon=icons.INFO)
            else:
                layout.label(text="Start a render to get a suggested clamp value", icon=icons.INFO)
        else:
            # Show a button that can be used to set the optimal clamp value
            op_text = "Set Suggested Value: %f" % config.path.suggested_clamping_value
            layout.operator("luxcore.set_suggested_clamping_value", text=op_text)


def compatible_panels():
    panels = [
        "RENDER_PT_color_management",
        "RENDER_PT_color_management_curves",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
    # We append our draw function to the existing Blender render panel
    RENDER_PT_context.append(luxcore_render_draw)
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")


def unregister():
    RENDER_PT_context.remove(luxcore_render_draw)
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")
