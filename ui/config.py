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

            if config.path.suggested_clamping_value == -1:
                # Optimal clamp value not yet found, need to start a render first
                if config.path.use_clamping:
                    # Can't compute optimal value if clamping is enabled
                    layout.label("Render without clamping to get suggested clamp value!", icon="ERROR")
                else:
                    layout.label("Start a render to get a suggested clamp value", icon="INFO")
            else:
                # Show a button that can be used to set the optimal clamp value
                op_text = "Set Suggested Value: %f" % config.path.suggested_clamping_value
                layout.operator("luxcore.set_suggested_clamping_value", text=op_text)

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

                if config.sampler == "SOBOL":
                    layout.prop(config, "sobol_adaptive_strength", slider=True)
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

    def _draw_cpu_settings(self, layout, context):
        # CPU settings for native C++ threads
        row = layout.row(align=True)
        row.prop(context.scene.render, "threads_mode", expand=True)
        sub = row.row(align=True)
        sub.enabled = context.scene.render.threads_mode == 'FIXED'
        sub.prop(context.scene.render, "threads")

    def _show_hybrid_metropolis_warning(self, context):
        config = context.scene.luxcore.config
        opencl = context.scene.luxcore.opencl
        return (config.engine == "PATH" and config.device == "OCL"
                and config.sampler == "METROPOLIS" and opencl.use_native_cpu)

    def draw_header(self, context):
        if self._show_hybrid_metropolis_warning(context):
            self.layout.label("", icon="ERROR")

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        opencl = context.scene.luxcore.opencl

        if config.engine == "PATH" and config.device == "OCL":
            if not opencl.devices:
                layout.label("No OpenCL Devices available.", icon="ERROR")
                layout.operator("luxcore.update_opencl_devices")

            gpu_devices = [device for device in opencl.devices if device.type == "OPENCL_GPU"]
            # We don't show OpenCL CPU devices, we just need them to check if there are other devices
            cpu_devices = [device for device in opencl.devices if device.type == "OPENCL_CPU"]
            other_devices = set(opencl.devices) - (set(gpu_devices) | set(cpu_devices))

            box = layout.box()
            box.label("GPU Devices:")
            self._draw_devices(box, gpu_devices)

            # This probably never happens
            if other_devices:
                col = layout.column(align=True)
                box = col.box()
                box.label("Other Devices")
                box = col.box()
                self._draw_devices(box, other_devices)

            has_gpus = any([device.enabled for device in gpu_devices])
            has_others = any([device.enabled for device in other_devices])
            if not has_gpus and not has_others:
                layout.label("Select at least one OpenCL device!", icon="ERROR")

            col = layout.column(align=True)
            col.prop(opencl, "use_native_cpu", toggle=True)
            if opencl.use_native_cpu:
                box = col.box()
                self._draw_cpu_settings(box, context)

                if self._show_hybrid_metropolis_warning(context):
                    col = box.column(align=True)
                    col.label("CPU should be disabled if Metropolis", icon="ERROR")
                    col.label("sampler is used (can cause artifacts)")
        else:
            col = layout.column()
            col.label(text="CPU Threads:")
            self._draw_cpu_settings(col, context)
