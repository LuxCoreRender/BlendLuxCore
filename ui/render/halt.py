from bl_ui.properties_render import RenderButtonsPanel
from bl_ui.properties_view_layer import ViewLayerButtonsPanel
from bpy.types import Panel
from ... import utils
from ...utils import ui as utils_ui
from .. import icons
from ..icons import icon_manager
from .sampling import calc_samples_per_pass


def draw(layout, context, halt):
    layout.active = halt.enable
    
    layout.prop(halt, "use_time")
    col = layout.column(align=True)
    col.active = halt.use_time
    col.prop(halt, "time")

    if halt.use_time and halt.time > 60:
        time_humanized = utils_ui.humanize_time(halt.time)

        col = layout.column(align=True)        
        col.label(text=time_humanized, icon="TIME")

    layout.prop(halt, "use_samples")
    col = layout.column(align=True)
    col.active = halt.use_samples
    col.prop(halt, "samples")

    config = context.scene.luxcore.config
    denoiser = context.scene.luxcore.denoiser

    using_hybridbackforward = utils.using_hybridbackforward(context.scene)
    using_only_lighttracing = config.using_only_lighttracing()

    if halt.use_samples:
        samples_per_pass = calc_samples_per_pass(config)
        
        if config.engine == "PATH" and config.use_tiles:
            # some special warnings about tile path usage
            if config.tile.multipass_enable and halt.samples % samples_per_pass != 0:
                layout.label(text="Should be a multiple of %d" % samples_per_pass, icon=icons.WARNING)

            if denoiser.enabled and denoiser.type == "BCD":
                # BCD Denoiser needs one warmup pass plus at least one sample collecting pass
                min_samples = samples_per_pass * 2
            else:
                min_samples = samples_per_pass

            if halt.samples < min_samples:
                layout.label(text="Use at least %d samples!" % min_samples, icon=icons.WARNING)

            if not config.tile.multipass_enable and halt.samples > min_samples:
                layout.label(text="Samples halt condition overriden by disabled multipass", icon=icons.INFO)
        elif config.get_sampler() in {"SOBOL", "RANDOM"} and config.using_out_of_core() or config.sampler_pattern == "CACHE_FRIENDLY":
            if halt.samples % samples_per_pass != 0:
                layout.label(text="Should be a multiple of %d" % samples_per_pass, icon=icons.WARNING)

            if denoiser.enabled and denoiser.type == "BCD":
                # BCD Denoiser needs one warmup pass plus at least one sample collecting pass
                min_samples = samples_per_pass * 2
            else:
                min_samples = samples_per_pass

            if halt.samples < min_samples:
                layout.label(text="Use at least %d samples!" % min_samples, icon=icons.WARNING)

    if using_hybridbackforward and not using_only_lighttracing:
        layout.prop(halt, "use_light_samples")
        col = layout.column(align=True)
        col.active = halt.use_light_samples
        col.prop(halt, "light_samples")

    layout.prop(halt, "use_noise_thresh")
    col = layout.column(align=True)
    if halt.use_noise_thresh:
        col.prop(halt, "noise_thresh")
        col.prop(halt, "noise_thresh_warmup")
        col.prop(halt, "noise_thresh_step")


class LUXCORE_RENDER_PT_halt_conditions(Panel, RenderButtonsPanel):
    """
    These are the global halt conditions shown in the render settings
    """

    bl_label = "Halt Conditions"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 70

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))
        halt = context.scene.luxcore.halt
        col = layout.column(align=True)
        col.prop(halt, "enable", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        config = context.scene.luxcore.config
        halt = context.scene.luxcore.halt
        draw(layout, context, halt)

        layers = context.scene.view_layers
        overriding_layers = [layer for layer in layers if layer.use and layer.luxcore.halt.enable]

        if overriding_layers:
            layout.separator()

            col = layout.column(align=True)
            row = col.row()
            split = row.split(factor=0.8)
            split.label(text="View Layers Overriding Halt Conditions:")
            op = split.operator("luxcore.switch_space_data_context",
                                text="Show", icon="RENDERLAYERS")
            op.target = "VIEW_LAYER"

            using_hybridbackforward = utils.using_hybridbackforward(context.scene)
            using_only_lighttracing = config.using_only_lighttracing()

            for layer in overriding_layers:
                halt = layer.luxcore.halt
                conditions = []

                if halt.use_time:
                    conditions.append("Time (%ds)" % halt.time)
                if halt.use_samples:
                    conditions.append("Samples (%d)" % halt.samples)
                if (halt.use_light_samples and using_hybridbackforward
                        and not using_only_lighttracing):
                    conditions.append("Light Path Samples (%d)" % halt.light_samples)
                if halt.use_noise_thresh:
                    conditions.append("Noise (%d)" % halt.noise_thresh)

                if conditions:
                    text = layer.name + ": " + ", ".join(conditions)
                    col.label(text=text, icon="RENDERLAYERS")
                else:
                    text = layer.name + ": No Halt Condition!"
                    col.label(text=text, icon=icons.ERROR)


class LUXCORE_RENDERLAYER_PT_halt_conditions(Panel, ViewLayerButtonsPanel):
    """
    These are the per-renderlayer halt condition settings,
    they can override the global settings and are shown in the renderlayer settings
    """

    bl_label = "Override Halt Conditions"
    bl_order = 40
    COMPAT_ENGINES = {"LUXCORE"}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        vl = context.view_layer
        halt = vl.luxcore.halt
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))
        col = layout.column(align=True)
        col.prop(halt, "enable", text="")

    def draw(self, context):
        vl = context.view_layer
        halt = vl.luxcore.halt
        draw(self.layout, context, halt)
