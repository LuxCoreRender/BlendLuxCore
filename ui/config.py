from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from .. import utils
from . import icons


class LUXCORE_RENDER_PT_config(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Config"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        denoiser = context.scene.luxcore.denoiser

        # Filesaver
        # TODO: we might want to move this to a more appropriate place later
        row = layout.row()
        split = row.split(percentage=0.7)
        split.prop(config, "use_filesaver")
        if config.use_filesaver:
            split.prop(config, "filesaver_format")
            layout.prop(config, "filesaver_path")
            layout.separator()

        # Device
        row_device = layout.row()
        row_device.enabled = config.engine == "PATH"
        row_device.label("Device:")

        if config.engine == "PATH":
            row_device.prop(config, "device", expand=True)

            if config.device == "OCL" and not utils.is_opencl_build():
                # pyluxcore was compiled without OpenCL support
                layout.label("No OpenCL support in this BlendLuxCore version", icon=icons.ERROR)
        else:
            row_device.prop(config, "bidir_device", expand=True)

        # Engine
        row_engine = layout.row()
        row_engine.label("Engine:")
        row_engine.prop(config, "engine", expand=True)

        if config.engine == "PATH":
            # Path options
            col = layout.column(align=True)
            col.prop(config.path, "depth_total")
            subrow = col.row(align=True)
            subrow.prop(config.path, "depth_diffuse")
            subrow.prop(config.path, "depth_glossy")
            subrow.prop(config.path, "depth_specular")

            self.draw_clamp_settings(layout, config)

            layout.prop(config, "use_tiles")

            if config.use_tiles:
                layout.label("Tiled path uses special sampler", icon=icons.INFO)
                row = layout.row(align=True)
                row.prop(config.tile, "size")
                row.prop(config.tile, "path_sampling_aa_size")

                if utils.use_two_tiled_passes(context.scene):
                    layout.label("(Doubling amount of samples because of denoiser)")

                layout.prop(config.tile, "multipass_enable")
                if config.tile.multipass_enable:
                    col = layout.column(align=True)
                    col.prop(config.tile, "multipass_convtest_threshold")
                    col.prop(config.tile, "multipass_convtest_threshold_reduction")
                    col.prop(config.tile, "multipass_convtest_warmup")
        else:
            # Bidir options
            row_depths = layout.row(align=True)
            row_depths.prop(config, "bidir_path_maxdepth")
            row_depths.prop(config, "bidir_light_maxdepth")

            self.draw_clamp_settings(layout, config)

        # Sampler settings
        if not (config.engine == "PATH" and config.use_tiles):
            row_sampler = layout.row()
            row_sampler.label("Sampler:")
            row_sampler.prop(config, "sampler", expand=True)

            if config.sampler in {"SOBOL", "RANDOM"}:
                col = layout.column(align=True)
                col.prop(config, "sobol_adaptive_strength", slider=True)
                if config.sobol_adaptive_strength > 0:
                    col.prop(config.noise_estimation, "warmup")
                    col.prop(config.noise_estimation, "step")
            elif config.sampler == "METROPOLIS":
                if denoiser.enabled and denoiser.type == "BCD":
                    layout.label("Can lead to artifacts in the denoiser!", icon=icons.WARNING)

                self.draw_metropolis_props(layout, config)

        # Filter settings
        filter_forced_none = denoiser.enabled and config.engine == "BIDIR" and config.filter != "NONE"
        if filter_forced_none:
            layout.label('Filter set to "None" (required by denoiser)', icon=icons.INFO)
        row = layout.row()
        row.active = not filter_forced_none
        row.prop(config, "filter")
        sub = row.row()
        sub.active = config.filter != "NONE"
        sub.prop(config, "filter_width")
        if config.filter == "GAUSSIAN":
            layout.prop(config, "gaussian_alpha")

        # Seed settings
        row = layout.row(align=True)
        sub = row.row(align=True)
        sub.active = not config.use_animated_seed
        sub.prop(config, "seed")
        row.prop(config, "use_animated_seed", icon="TIME", toggle=True)

        # Light strategy
        ls_layout = layout.box() if config.light_strategy == "DLS_CACHE" else layout
        ls_layout.prop(config, "light_strategy")

        if config.light_strategy == "DLS_CACHE":
            dls_cache = config.dls_cache
            col = ls_layout.column(align=True)
            col.prop(dls_cache, "entry_radius_auto")
            if not dls_cache.entry_radius_auto:
                col.prop(dls_cache, "entry_radius")
            col.prop(dls_cache, "entry_warmupsamples")
            ls_layout.prop(dls_cache, "show_advanced", toggle=True)

            if dls_cache.show_advanced:
                col = ls_layout.column(align=True)
                col.label("Entry Settings:")
                col.prop(dls_cache, "entry_normalangle")
                col.prop(dls_cache, "entry_maxpasses")
                col.prop(dls_cache, "entry_convergencethreshold")
                col.prop(dls_cache, "entry_volumes_enable")

                col = ls_layout.column(align=True)
                col.label("General Cache Settings:")
                col.prop(dls_cache, "lightthreshold")
                col.prop(dls_cache, "targetcachehitratio")
                col.prop(dls_cache, "maxdepth")
                col.prop(dls_cache, "maxsamplescount")

    def draw_clamp_settings(self, layout, config):
        split = layout.split()
        split.prop(config.path, "use_clamping")
        col = split.column()
        col.enabled = config.path.use_clamping
        col.prop(config.path, "clamping")

        if config.path.suggested_clamping_value == -1:
            # Optimal clamp value not yet found, need to start a render first
            if config.path.use_clamping:
                # Can't compute optimal value if clamping is enabled
                layout.label("Render without clamping to get suggested clamp value", icon=icons.INFO)
            else:
                layout.label("Start a render to get a suggested clamp value", icon=icons.INFO)
        else:
            # Show a button that can be used to set the optimal clamp value
            op_text = "Set Suggested Value: %f" % config.path.suggested_clamping_value
            layout.operator("luxcore.set_suggested_clamping_value", text=op_text)

    def draw_metropolis_props(self, layout, config):
        col = layout.column(align=True)
        col.prop(config, "metropolis_largesteprate", slider=True)
        col.prop(config, "metropolis_maxconsecutivereject")
        col.prop(config, "metropolis_imagemutationrate", slider=True)
