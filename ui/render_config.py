from . import bpy
from . import icons
from .. import utils

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
    if config.device == "OCL" and not utils.is_opencl_build():
        # pyluxcore was compiled without OpenCL support
        col_device.label(text="No OpenCL support in this BlendLuxCore version", icon=icons.ERROR)
    else:
        col_device.prop(config, "device", text="Device")
        col_device.active = config.engine == "PATH"

    # Engine
    col = layout.column(align=True)
    col.prop(config, "engine", expand=False)
    col.active = True

    if config.device == "OCL":
        col.active = False

    # Buttons for Network Render and Wiki
    flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
    col = flow.column(align=True)
    col.operator("luxcore.start_pyluxcoretools")
    col = flow.column(align=True)
    op = col.operator("luxcore.open_website", icon=icons.URL, text="Wiki")
    op.url = "https://wiki.luxcorerender.org/BlendLuxCore_Network_Rendering"

            
class LUXCORE_RENDER_PT_filter(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Pixel Filter"
    bl_order = 4

    def draw(self, context):
        layout = self.layout

        config = context.scene.luxcore.config
        denoiser = context.scene.luxcore.denoiser
        scene = context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False      

        # Filter settings

        filter_forced_none = denoiser.enabled and config.engine == "BIDIR" and config.filter != "NONE"
        if filter_forced_none:
            layout.label(text='Filter set to "None" (required by denoiser)', icon=icons.INFO)
        
        col = layout.column(align=True)      
        col.enabled = not filter_forced_none        
        col.prop(config, "filter")

        col = layout.column(align=True)      
        col.enabled = config.filter != "NONE"
        col.prop(config, "filter_width")
        if config.filter == "GAUSSIAN":
            layout.prop(config, "gaussian_alpha")


class LUXCORE_RENDER_PT_light_strategy(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Light Strategy"
    bl_order = 3

    def draw(self, context):
        layout = self.layout

        config = context.scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False      

        # Light strategy        
        layout.prop(config, "light_strategy")

        if config.light_strategy == "DLS_CACHE":
            dls_cache = config.dls_cache
            col = layout.column(align=True)
            col.prop(dls_cache, "entry_radius_auto")
            if not dls_cache.entry_radius_auto:
                col.prop(dls_cache, "entry_radius")
            col.prop(dls_cache, "entry_warmupsamples")
            layout.prop(dls_cache, "show_advanced", toggle=True)

            if dls_cache.show_advanced:
                col = layout.column(align=True)
                col.label(text="Entry Settings:")
                col.prop(dls_cache, "entry_normalangle")
                col.prop(dls_cache, "entry_maxpasses")
                col.prop(dls_cache, "entry_convergencethreshold")
                col.prop(dls_cache, "entry_volumes_enable")

                col = layout.column(align=True)
                col.label(text="General Cache Settings:")
                col.prop(dls_cache, "lightthreshold")
                col.prop(dls_cache, "targetcachehitratio")
                col.prop(dls_cache, "maxdepth")
                col.prop(dls_cache, "maxsamplescount")


class LUXCORE_RENDER_PT_lightpaths(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Light Paths"
    bl_order = 2

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
    bl_parent_id = "LUXCORE_RENDER_PT_lightpaths"
    lux_predecessor = "LUXCORE_RENDER_PT_lightpaths_bounces"
    bl_label = "Add Light Tracing"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True
        # return not context.scene.luxcore.config.use_tiles

    def error(self, context):
        use_native_cpu = context.scene.luxcore.opencl.use_native_cpu
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

        row = layout.row()
        if config.device == "CPU":
            row.prop(config.path, "hybridbackforward_lightpartition")
        elif self.error(context):
            col = layout.column()
            col.label(text='Enable "Use CPUs" in LuxCore device settings', icon=icons.WARNING)
            col.prop(context.scene.luxcore.opencl, "use_native_cpu", toggle=True)


class LUXCORE_RENDER_PT_clamping(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDER_PT_lightpaths"
    lux_predecessor = "LUXCORE_RENDER_PT_add_light_tracing"
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
      
        layout.enabled = config.path.use_clamping
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


class LUXCORE_RENDER_PT_lightpaths_advanced(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDER_PT_lightpaths"
    lux_predecessor = "LUXCORE_RENDER_PT_clamping"
    bl_label = "Advanced"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        config = context.scene.luxcore.config
        denoiser = context.scene.luxcore.denoiser
        scene = context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False

        # Seed settings
        row = layout.row(align=True)      
        row.active = not config.use_animated_seed
        row.prop(config, "seed")
        row.prop(config, "use_animated_seed", text="", icon="TIME", toggle=True)

        # Sampler settings
        if not (config.engine == "PATH" and config.use_tiles):
            row_sampler = layout.row()
            row_sampler.prop(config, "sampler", expand=False)

            if config.sampler in {"SOBOL", "RANDOM"}:
                col = layout.column(align=True)
                col.prop(config, "sobol_adaptive_strength", slider=True)
                if config.sobol_adaptive_strength > 0:
                    col.prop(config.noise_estimation, "warmup")
                    col.prop(config.noise_estimation, "step")
            elif config.sampler == "METROPOLIS":
                if denoiser.enabled and denoiser.type == "BCD":
                    layout.label(text="Can lead to artifacts in the denoiser!", icon=icons.WARNING)

                col = layout.column(align=True)
                col.prop(config, "metropolis_largesteprate", slider=True)
                col.prop(config, "metropolis_maxconsecutivereject")
                col.prop(config, "metropolis_imagemutationrate", slider=True)
        else:
            row_sampler = layout.row()
            row_sampler.label(text="Tiled path uses special sampler", icon=icons.INFO)


class LUXCORE_RENDER_PT_lightpaths_tiled(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDER_PT_lightpaths"
    lux_predecessor = "LUXCORE_RENDER_PT_lightpaths_advanced"
    bl_label = "Tiled"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):        
        config = context.scene.luxcore.config
        return config.engine == "PATH"

    def draw_header(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        layout.prop(config, "use_tiles", text="")

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        
        layout.enabled = config.use_tiles
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(config.tile, "size")
        col.prop(config.tile, "path_sampling_aa_size")

        if utils.use_two_tiled_passes(context.scene):
            layout.label(text="(Doubling amount of samples because of denoiser)")


class LUXCORE_RENDER_PT_lightpaths_tiled_multipass(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDER_PT_lightpaths_tiled"
    bl_label = "Multipass"
    bl_options = {'DEFAULT_CLOSED'}    

    @classmethod
    def poll(cls, context):        
        config = context.scene.luxcore.config
        return config.use_tiles

    def draw_header(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        layout.prop(config.tile, "multipass_enable", text="")
      
    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False      
      
        layout.enabled = config.tile.multipass_enable

        col = layout.column(align=True)
        col.prop(config.tile, "multipass_convtest_threshold")
        col.prop(config.tile, "multipass_convtest_threshold_reduction")
        col.prop(config.tile, "multipass_convtest_warmup")


class LUXCORE_RENDER_PT_filesaver(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Filesaver"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

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

