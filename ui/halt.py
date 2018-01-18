from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from .. import utils


class LUXCORE_RENDER_PT_halt_conditions(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Halt Conditions"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        self.layout.prop(context.scene.luxcore.halt, "enable", text="")

    def draw(self, context):
        layout = self.layout
        halt = context.scene.luxcore.halt
        layout.active = halt.enable

        row = layout.row()
        row.prop(halt, "use_time")
        split = row.split()
        split.active = halt.use_time
        split.prop(halt, "time")

        time_humanized = utils.humanize_time(halt.time)
        row = layout.row()
        row.active = halt.use_time
        row.label(time_humanized, icon="TIME")

        row = layout.row()
        row.prop(halt, "use_samples")
        split = row.split()
        split.active = halt.use_samples
        split.prop(halt, "samples")

