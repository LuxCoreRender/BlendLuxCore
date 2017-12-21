import datetime

import bl_ui
from bl_ui.properties_render import RenderButtonsPanel
import bpy
from bpy.types import Panel


class LuxCoreHaltConditions(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "LuxCore Halt Conditions"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        self.layout.prop(context.scene.luxcore.halt, "enable", text="")

    def draw(self, context):
        layout = self.layout
        halt = context.scene.luxcore.halt
        layout.enabled = halt.enable

        row = layout.row()
        row.prop(halt, "use_time")
        split = row.split()
        split.enabled = halt.use_time
        split.prop(halt, "time")

        m, s = divmod(halt.time, 60)
        h, m = divmod(m, 60)
        time_humanized = "%d hours, %d minutes, %d seconds" % (h, m, s)
        row = layout.row()
        row.enabled = halt.use_time
        row.label(time_humanized, icon="TIME")

        row = layout.row()
        row.prop(halt, "use_samples")
        split = row.split()
        split.enabled = halt.use_samples
        split.prop(halt, "samples")

