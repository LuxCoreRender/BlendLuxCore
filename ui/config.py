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

    def _draw_devices(self, layout, devices):
        for device in devices:
            layout.prop(device, "enabled", text=device.name)

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        opencl = context.scene.luxcore.opencl

        if config.engine == "PATH" and config.device == "OCL":
            if not opencl.devices:
                layout.label("No OpenCL Devices available.", icon="ERROR")
                layout.operator("luxcore.update_opencl_devices")

            gpu_devices = [device for device in opencl.devices if device.type == "OPENCL_GPU"]
            cpu_devices = [device for device in opencl.devices if device.type == "OPENCL_CPU"]
            other_devices = set(opencl.devices) - (set(gpu_devices) | set(cpu_devices))

            if gpu_devices:
                col = layout.column(align=True)
                col.prop(opencl, "use_gpu", toggle=True)

                if opencl.use_gpu:
                    box = col.box()
                    box.active = opencl.use_gpu
                    self._draw_devices(box, gpu_devices)

            if cpu_devices:
                col = layout.column(align=True)
                col.prop(opencl, "use_cpu", toggle=True)

                if opencl.use_cpu:
                    box = col.box()
                    box.active = opencl.use_cpu
                    self._draw_devices(box, cpu_devices)

            if other_devices:
                col = layout.column(align=True)
                box = col.box()
                box.label("Other Devices")
                box = col.box()
                box.active = opencl.use_gpu
                self._draw_devices(box, other_devices)

            has_cpus = any([device.enabled for device in cpu_devices]) and opencl.use_cpu
            has_gpus = any([device.enabled for device in gpu_devices]) and opencl.use_gpu
            has_others = any([device.enabled for device in other_devices])
            if not has_cpus and not has_gpus and not has_others:
                layout.label("Select at least one OpenCL device!", icon="ERROR")

        elif config.device == "CPU" or config.engine == "BIDIR":
            layout.label(text="CPU Threads:")
            row = layout.row(align=True)
            row.prop(context.scene.render, "threads_mode", expand=True)
            sub = row.row(align=True)
            sub.enabled = context.scene.render.threads_mode == 'FIXED'
            sub.prop(context.scene.render, "threads")
