import bpy
from .. import icons
from ... import utils
from ...export.config import SamplingOverlap

from bpy.types import Panel
from bl_ui.properties_render import RenderButtonsPanel


def calc_samples_per_pass(config):
    if config.using_tiled_path():
        return config.tile.path_sampling_aa_size**2
    elif config.get_sampler() in {"SOBOL", "RANDOM"}:
        if config.using_out_of_core():
            return int(config.out_of_core_supersampling) * SamplingOverlap.OUT_OF_CORE
        else:
            if config.sampler_pattern == "PROGRESSIVE":
                return SamplingOverlap.PROGRESSIVE
            elif config.sampler_pattern == "CACHE_FRIENDLY":
                return SamplingOverlap.CACHE_FRIENDLY
    return -1


class LUXCORE_RENDER_PT_sampling(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Sampling"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 25

    def draw(self, context):
        layout = self.layout

        config = context.scene.luxcore.config
        sampler = config.get_sampler()
        denoiser = context.scene.luxcore.denoiser

        layout.use_property_split = True
        layout.use_property_decorate = False

        if config.using_tiled_path():
            row = layout.row()
            row.label(text="Tiled path uses special sampler", icon=icons.INFO)
            
            col = layout.column(align=True)
            col.prop(config.tile, "size")
            col.prop(config.tile, "path_sampling_aa_size")

            if utils.use_two_tiled_passes(context.scene):
                layout.label(text="(Doubling amount of samples because of denoiser)")
        else:
            # Not tiled, regular sampling
            row = layout.row()
            
            if config.device == "OCL" and config.engine == "PATH":
                row.prop(config, "sampler_gpu")
            else:
                row.prop(config, "sampler")

            if sampler in {"SOBOL", "RANDOM"}:
                col = layout.column()
                col.active = not config.using_out_of_core()
                col.prop(config, "sampler_pattern")
                
                if config.device == "OCL":
                    col = layout.column()
                    col.prop(config, "out_of_core")
                    if config.out_of_core:
                        col.prop(config, "out_of_core_supersampling")
            elif sampler == "METROPOLIS":
                if denoiser.enabled and denoiser.type == "BCD":
                    layout.label(text="Can lead to artifacts in the denoiser!", icon=icons.WARNING)

                col = layout.column(align=True)
                col.prop(config, "metropolis_largesteprate", slider=True)
                col.prop(config, "metropolis_maxconsecutivereject")
                col.prop(config, "metropolis_imagemutationrate", slider=True)
        
        # Samples (per pixel) per pass info
        
        samples_per_pass = calc_samples_per_pass(config)
        if samples_per_pass != -1:
            row = layout.row()
            row.alignment = "RIGHT"
            row.label(text=f"Samples per Pass: {samples_per_pass}")


class LUXCORE_RENDER_PT_sampling_tiled_multipass(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDER_PT_sampling"
    bl_label = "Tile Multipass"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        config = context.scene.luxcore.config
        return config.using_tiled_path()

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


class LUXCORE_RENDER_PT_sampling_adaptivity(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDER_PT_sampling"
    lux_predecessor = "LUXCORE_RENDER_PT_sampling_tiled_multipass"
    bl_label = "Adaptive Sampling"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        config = context.scene.luxcore.config
        return config.get_sampler() in {"SOBOL", "RANDOM"} and not config.using_tiled_path()

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        layout.use_property_split = True
        layout.use_property_decorate = False
        
        col = layout.column(align=True)
        col.prop(config, "sobol_adaptive_strength", slider=True)
        
        if config.sobol_adaptive_strength > 0:
            col.prop(config.noise_estimation, "warmup")
            col.prop(config.noise_estimation, "step")


class LUXCORE_RENDER_PT_sampling_advanced(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_parent_id = "LUXCORE_RENDER_PT_sampling"
    lux_predecessor = "LUXCORE_RENDER_PT_sampling_adaptivity"
    bl_label = "Advanced"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        denoiser = context.scene.luxcore.denoiser

        layout.use_property_split = True
        layout.use_property_decorate = False
        
        # Seed settings
        row = layout.row(align=True)      
        row.active = not config.use_animated_seed
        row.prop(config, "seed")
        row.prop(config, "use_animated_seed", text="", icon="TIME", toggle=True)
        
        # Light strategy
        col = layout.column()
        if config.dls_cache.enabled:
            col.label(text="Using direct light sampling cache", icon=icons.INFO)
            col = layout.column()
            col.active = False
        
        col.prop(config, "light_strategy")
        
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
        elif config.filter == "SINC":
            layout.prop(config, "sinc_tau")
        
        # Tiled path
        if config.engine == "PATH":
            layout.prop(config, "use_tiles")
