#from bpy.types import RENDER_PT_context
from . import bpy
from . import icons
from .. import utils

from bpy.types import Panel
from bl_ui.properties_render import RENDER_PT_context
from bl_ui.properties_render import RenderButtonsPanel

# Note: The main LuxCore config UI is defined in ui/config.py
# Each of the other render panels is also defined in their
# own specific files in the ui/ folder.

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
        col_device.enabled = config.engine == "PATH"

    # Buttons for Network Render and Wiki
    row = layout.row(align=True)
    row.alignment = 'LEFT'
    flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
    row = flow.row()
    row.operator("luxcore.start_pyluxcoretools")
    row = flow.row()
    op = row.operator("luxcore.open_website", icon=icons.URL, text="Wiki")
    op.url = "https://wiki.luxcorerender.org/BlendLuxCore_Network_Rendering"


def draw_samples_info(layout, context):
    config = context.scene.luxcore.config
    engine = config.engine

    # Calculate sample values
    if engine == 'PATH':
        total    = config.path.depth_total      
        diffuse  = config.path.depth_diffuse
        glossy   = config.path.depth_glossy
        specular = config.path.depth_specular
       
        # Draw interface
        # Do not draw for progressive, when Square Samples are disabled
        col = layout.column(align=True)
        col.scale_y = 0.6
        col.label(text="Total Samples:")
        col.separator()
        col.label(text="%s Total, %s Diffuse, %s Glossy, %s Specular" %
                  (total, diffuse * total, glossy * total, specular * total))

            
#class LUXCORE_RENDER_PT_config(RenderButtonsPanel, Panel):
#     COMPAT_ENGINES = {"LUXCORE"}
#     bl_label = "LuxCore Config"
#
#     @classmethod
#     def poll(cls, context):
#         return context.scene.render.engine == "LUXCORE"
#
#     def draw(self, context):
#         layout = self.layout
#         config = context.scene.luxcore.config
#         denoiser = context.scene.luxcore.denoiser
#
#         # Filesaver
#         # TODO: we might want to move this to a more appropriate place later
#         row = layout.row()
#         split = row.split(factor=0.7)
#         split.prop(config, "use_filesaver")
#         if config.use_filesaver:
#             split.prop(config, "filesaver_format")
#             layout.prop(config, "filesaver_path")
#             layout.separator()
#
#         # Light strategy
#         ls_layout = layout.box() if config.light_strategy == "DLS_CACHE" else layout
#         ls_layout.prop(config, "light_strategy")
#
#         if config.light_strategy == "DLS_CACHE":
#             dls_cache = config.dls_cache
#             col = ls_layout.column(align=True)
#             col.prop(dls_cache, "entry_radius_auto")
#             if not dls_cache.entry_radius_auto:
#                 col.prop(dls_cache, "entry_radius")
#             col.prop(dls_cache, "entry_warmupsamples")
#             ls_layout.prop(dls_cache, "show_advanced", toggle=True)
#
#             if dls_cache.show_advanced:
#                 col = ls_layout.column(align=True)
#                 col.label(text="Entry Settings:")
#                 col.prop(dls_cache, "entry_normalangle")
#                 col.prop(dls_cache, "entry_maxpasses")
#                 col.prop(dls_cache, "entry_convergencethreshold")
#                 col.prop(dls_cache, "entry_volumes_enable")
#
#                 col = ls_layout.column(align=True)
#                 col.label(text="General Cache Settings:")
#                 col.prop(dls_cache, "lightthreshold")
#                 col.prop(dls_cache, "targetcachehitratio")
#                 col.prop(dls_cache, "maxdepth")
#                 col.prop(dls_cache, "maxsamplescount")
#


class LUXCORE_RENDER_PT_filter(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Pixel Filter"

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


class LUXCORE_RENDER_PT_sampling(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Sampling"

    def draw(self, context):
        layout = self.layout

        config = context.scene.luxcore.config
        denoiser = context.scene.luxcore.denoiser
        scene = context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(config, "engine", expand=False)
        col.enabled = True
      
        # Engine
        if config.device == "OCL":
            col.enabled = False

        if config.engine == "PATH":
            # Path options
            col = layout.column(align=True)
            col.prop(config.path, "depth_total")
        else:
            # Bidir options         
            col = layout.column(align=True)
            col.prop(config, "bidir_path_maxdepth")
            col.prop(config, "bidir_light_maxdepth")


class LUXCORE_RENDER_PT_sampling_sub_samples(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
#    bl_parent_id = "LUXCORE_RENDER_PT_sampling"
    bl_label = "Sub Samples"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):        
        config = context.scene.luxcore.config
        return config.engine == "PATH"

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False
      
        col = layout.column(align=True)
        col.prop(config.path, "depth_diffuse")
        col.prop(config.path, "depth_glossy")
        col.prop(config.path, "depth_specular")

        draw_samples_info(layout, context)


class LUXCORE_RENDER_PT_sampling_advanced(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
#    bl_parent_id = "LUXCORE_RENDER_PT_sampling"
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


class LUXCORE_RENDER_PT_sampling_tiled(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
#    bl_parent_id = "LUXCORE_RENDER_PT_sampling"
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


class LUXCORE_RENDER_PT_sampling_tiled_multipass(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
#   bl_parent_id = "LUXCORE_RENDER_PT_sampling_tiled"
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


class LUXCORE_RENDER_PT_clamping(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
#   bl_parent_id = "LUXCORE_RENDER_PT_sampling_tiled"
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


def compatible_panels():
    panels = [
        "RENDER_PT_color_management",
        "RENDER_PT_color_management_curves",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]

classes = (
    LUXCORE_RENDER_PT_sampling,
    LUXCORE_RENDER_PT_sampling_sub_samples,
    LUXCORE_RENDER_PT_sampling_advanced,
    LUXCORE_RENDER_PT_sampling_tiled,
    LUXCORE_RENDER_PT_sampling_tiled_multipass,
    LUXCORE_RENDER_PT_filter,
)

def register():
#    from bpy.utils import register_class
    # We append our draw function to the existing Blender render panel
    RENDER_PT_context.append(luxcore_render_draw)
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")

#    for cls in classes:
#       register_class(cls)
    


def unregister():
#    from bpy.utils import unregister_class
    RENDER_PT_context.remove(luxcore_render_draw)
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")

#   for cls in classes:
#      unregister_class(cls)
