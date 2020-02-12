from time import time
from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from . import icons
from ..utils import sarfis


def format_time(time, show_frame=True):
    frame, time_millis = time
    time_s = round(time_millis / 1000, 1)
    result = f"{time_s} s"
    if show_frame:
        result += f" (frame {frame})"
    return result


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

            col = layout.column(align=True)
            status = sarfis.Status.status
            col.label(text="Status: " + str(status))

            p = sarfis.Status.progress
            if p:
                completed = p.finished + p.errored
                percentage_completed = round(completed / p.frame_count * 100, 1)
                col.label(text=f"{completed}/{p.frame_count} ({percentage_completed}%)")
                if p.errored:
                    col.label(text=f"{p.errored} frames", icon=icons.WARNING)

                col.label(text=f"Times: Min {format_time(p.time_min)}, Max {format_time(p.time_max)}, Median {format_time(p.time_median, False)}")

                time_start = sarfis.Status.time_start
                if time_start:
                    time_end = sarfis.Status.time_end
                    if time_end is None:
                        time_end = time()
                    col.label(text=f"Elapsed Time: {round(time_end - time_start, 1)} s")
        else:
            layout.label(text="No jobs started yet")
