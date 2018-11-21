from bl_ui.properties_render import RenderButtonsPanel
from bl_ui.properties_render_layer import RenderLayerButtonsPanel
from bpy.types import Panel
from ..utils import ui as utils_ui
from . import icons


def draw(layout, context, halt):
    layout.active = halt.enable

    row = layout.row()
    row.prop(halt, "use_time")
    split = row.split()
    split.active = halt.use_time
    split.prop(halt, "time")

    time_humanized = utils_ui.humanize_time(halt.time)
    row = layout.row()
    row.active = halt.use_time
    row.label(time_humanized, icon="TIME")

    row = layout.row()
    row.prop(halt, "use_samples")
    split = row.split()
    split.active = halt.use_samples
    split.prop(halt, "samples")

    config = context.scene.luxcore.config
    is_adaptive_sampler = config.engine == "PATH" and config.sampler in {"SOBOL", "RANDOM"}
    show_adaptive_sampling_props = halt.use_noise_thresh and is_adaptive_sampler

    if show_adaptive_sampling_props:
        thresh_layout = layout.box()
    else:
        thresh_layout = layout

    row = thresh_layout.row()
    row.prop(halt, "use_noise_thresh")
    split = row.split()
    split.active = halt.use_noise_thresh
    split.prop(halt, "noise_thresh")

    if show_adaptive_sampling_props:
        row = thresh_layout.row(align=True)
        row.prop(halt, "noise_thresh_warmup")
        row.prop(halt, "noise_thresh_step")
        thresh_layout.prop(halt, "noise_thresh_use_filter")


class LUXCORE_RENDER_PT_halt_conditions(Panel, RenderButtonsPanel):
    """
    These are the global halt conditions shown in the render settings
    """

    bl_label = "LuxCore Halt Conditions"
    COMPAT_ENGINES = {"LUXCORE"}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        halt = context.scene.luxcore.halt
        self.layout.prop(halt, "enable", text="")

    def draw(self, context):
        layout = self.layout
        halt = context.scene.luxcore.halt
        draw(layout, context, halt)

        layers = context.scene.render.layers
        overriding_layers = [layer for layer in layers if layer.use and layer.luxcore.halt.enable]

        if overriding_layers:
            layout.separator()

            col = layout.column(align=True)
            row = col.row()
            split = row.split(percentage=0.8)
            split.label("Render Layers Overriding Halt Conditions:")
            op = split.operator("luxcore.switch_space_data_context",
                                text="Show", icon="RENDERLAYERS")
            op.target = "RENDER_LAYER"

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
                    col.label(text, icon="RENDERLAYERS")
                else:
                    text = layer.name + ": No Halt Condition!"
                    col.label(text, icon=icons.ERROR)


class LUXCORE_RENDERLAYER_PT_halt_conditions(Panel, RenderLayerButtonsPanel):
    """
    These are the per-renderlayer halt condition settings,
    they can override the global settings and are shown in the renderlayer settings
    """

    bl_label = "Override Halt Conditions"
    COMPAT_ENGINES = {"LUXCORE"}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        rl = context.scene.render.layers.active
        halt = rl.luxcore.halt
        self.layout.prop(halt, "enable", text="")

    def draw(self, context):
        rl = context.scene.render.layers.active
        halt = rl.luxcore.halt
        draw(self.layout, context, halt)
