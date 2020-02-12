from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from . import icons
from ..utils import sarfis


class LUXCORE_RENDER_PT_sarfis(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "SARFIS Render Farm"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        settings = scene.luxcore.sarfis
        layout.prop(settings, "output_dir")
        layout.prop(settings, "mode")
        if settings.mode == "single_frame":
            layout.label(text=f"Frame: {scene.frame_current}")
        else:
            col = layout.column(align=True)
            col.label(text=f"First Frame: {scene.frame_start}")
            col.label(text=f"Last Frame: {scene.frame_end}")
            col.label(text=f"Frame Count: {scene.frame_end - scene.frame_start + 1}")

        row = layout.row()
        row.operator("luxcore.sarfis_start", icon=icons.RENDER_STILL)
        if sarfis.Status.status == sarfis.Status.PAUSED:
            row.operator("luxcore.sarfis_resume", icon=icons.PLAY)
        else:
            row.operator("luxcore.sarfis_pause", icon=icons.PAUSE)
        row.operator("luxcore.sarfis_delete", icon=icons.TRASH)

        if sarfis.Status.job_id:
            layout.label(text="Job ID: " + sarfis.Status.job_id)  # TODO remove
            layout.label(text="Status: " + str(sarfis.Status.status))
        else:
            layout.label(text="No jobs started yet")
            layout.label(text="Status: " + str(sarfis.Status.status))  # TODO remove
