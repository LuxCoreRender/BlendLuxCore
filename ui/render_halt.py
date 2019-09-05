from bl_ui.properties_render import RenderButtonsPanel
from bl_ui.properties_view_layer import ViewLayerButtonsPanel
from bpy.types import Panel
from ..utils import ui as utils_ui
from . import icons


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

    if halt.use_samples and config.engine == "PATH" and config.use_tiles:
        # some special warnings about tile path usage
        aa = config.tile.path_sampling_aa_size
        samples_per_pass = aa**2

        if config.tile.multipass_enable and halt.samples % samples_per_pass != 0:
            layout.label(text="Should be a multiple of %d" % samples_per_pass, icon=icons.WARNING)

        if context.scene.luxcore.denoiser.enabled and context.scene.luxcore.denoiser.type == "BCD":
            # BCD Denoiser needs one warmup pass plus at least one sample collecting pass
            min_samples = samples_per_pass * 2
        else:
            min_samples = samples_per_pass

        if halt.samples < min_samples:
            layout.label(text="Use at least %d samples!" % min_samples, icon=icons.WARNING)

        if not config.tile.multipass_enable and halt.samples > min_samples:
            layout.label(text="Samples halt condition overriden by disabled multipass", icon=icons.INFO)

    col = layout.column(align=True)
    col.prop(halt, "use_noise_thresh")
    if halt.use_noise_thresh:
        col.prop(halt, "noise_thresh")
        col.prop(halt, "noise_thresh_warmup")
        col.prop(halt, "noise_thresh_step")


class LUXCORE_RENDER_PT_halt_conditions(Panel, RenderButtonsPanel):
    """
    These are the global halt conditions shown in the render settings
    """

    bl_label = "LuxCore Halt Conditions"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 10

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        halt = context.scene.luxcore.halt
        self.layout.prop(halt, "enable", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

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

            for layer in overriding_layers:
                halt = layer.luxcore.halt
                conditions = []

                if halt.use_time:
                    conditions.append("Time (%ds)" % halt.time)
                if halt.use_samples:
                    conditions.append("Samples (%d)" % halt.samples)
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
    bl_order = 4
    COMPAT_ENGINES = {"LUXCORE"}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        vl = context.view_layer
        halt = vl.luxcore.halt
        self.layout.prop(halt, "enable", text="")

    def draw(self, context):
        vl = context.view_layer
        halt = vl.luxcore.halt
        draw(self.layout, context, halt)
