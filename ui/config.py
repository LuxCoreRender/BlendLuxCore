from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel


class LUXCORE_RENDER_PT_config(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Config"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        # Filesaver
        # TODO: we might want to move this to a more appropriate place later
        row = layout.row()
        row.prop(config, "use_filesaver")
        if config.use_filesaver:
            row.prop(config, "filesaver_format")
            layout.prop(context.scene.render, "filepath")
            layout.separator()

        # Device
        row_device = layout.row()
        row_device.enabled = config.engine == "PATH"
        row_device.label("Device:")

        if config.engine == "PATH":
            row_device.prop(config, "device", expand=True)
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

            split = layout.split()
            split.prop(config.path, "use_clamping")
            col = split.column()
            col.enabled = config.path.use_clamping
            col.prop(config.path, "clamping")

            if config.path.optimal_clamping_value == -1:
                # Optimal clamp value not yet found, need to start a render first
                if config.path.use_clamping:
                    # Can't compute optimal value if clamping is enabled
                    layout.label("Render without clamping to find optimal clamp value!", icon="ERROR")
                else:
                    layout.label("Start a render to find the optimal clamp value", icon="INFO")
            else:
                # Show a button that can be used to set the optimal clamp value
                op_text = "Set Optimal Value: %f" % config.path.optimal_clamping_value
                layout.operator("luxcore.set_optimal_clamping_value", text=op_text)

            layout.prop(config, "use_tiles")

            if config.use_tiles:
                layout.label("Tiled path uses special sampler", icon="INFO")
                row = layout.row(align=True)
                row.prop(config.tile, "size")
                row.prop(config.tile, "path_sampling_aa_size")

                layout.prop(config.tile, "multipass_enable")
                if config.tile.multipass_enable:
                    col = layout.column(align=True)
                    col.prop(config.tile, "multipass_convtest_threshold")
                    col.prop(config.tile, "multipass_convtest_threshold_reduction")
                    # TODO do we need to expose this? In LuxBlend we didn't
                    # layout.prop(config.tile, "multipass_convtest_warmup")
            else:
                row_sampler = layout.row()
                row_sampler.label("Sampler:")
                row_sampler.prop(config, "sampler", expand=True)
        else:
            # Bidir options
            row_depths = layout.row(align=True)
            row_depths.prop(config, "bidir_path_maxdepth")
            row_depths.prop(config, "bidir_light_maxdepth")

            row_sampler = layout.row()
            row_sampler.enabled = False
            row_sampler.label("Sampler:")
            row_sampler.prop(config, "bidir_sampler", expand=True)

        # Filter settings
        row = layout.row()
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


class LUXCORE_RENDER_PT_device_settings(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Device Settings"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        if config.engine == "PATH" and config.device == "OCL":
            layout.label("OpenCL Options:")
            layout.prop(config.opencl, "use_cpu")
            layout.prop(config.opencl, "use_gpu")
        elif config.device == "CPU" or config.engine == "BIDIR":
            layout.label(text="CPU Threads:")
            row = layout.row(align=True)
            row.prop(context.scene.render, "threads_mode", expand=True)
            sub = row.row(align=True)
            sub.enabled = context.scene.render.threads_mode == 'FIXED'
            sub.prop(context.scene.render, "threads")
