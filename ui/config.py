import bl_ui
from bl_ui.properties_render import RenderButtonsPanel
import bpy
from bpy.types import Panel


class LuxCoreConfig(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Config"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

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

            layout.prop(config, "use_tiles")

            if config.use_tiles:
                layout.label("Tiled path uses special sampler", icon="INFO")
                # TODO for some reason luxcore needs much RAM with small tiles
                # and few RAM with large tiles... maybe a bug? Or am I doing something wrong?
                # Also the startup time with small tiles is very long
                layout.prop(config.tile, "size")
                layout.prop(config.tile, "path_sampling_aa_size")
                layout.prop(config.tile, "multipass_enable")
                if config.tile.multipass_enable:
                    layout.prop(config.tile, "multipass_convtest_threshold")
                    layout.prop(config.tile, "multipass_convtest_threshold_reduction")
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
        row.prop(config, "use_filter")
        split = row.split()
        split.active = config.use_filter
        split.prop(config, "filter_width")

class LuxCoreDeviceSettings(RenderButtonsPanel, Panel):
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
