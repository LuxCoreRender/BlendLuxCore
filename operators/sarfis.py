import bpy
import os
from .. import utils
from ..utils import sarfis
from ..utils.sarfis import Status


class LUXCORE_OT_sarfis_start(bpy.types.Operator):
    bl_idname = "luxcore.sarfis_start"
    bl_label = "Start"
    bl_description = ""

    @classmethod
    def poll(self, context):
        return Status.status in {None, Status.FINISHED}

    def execute(self, context):
        scene = context.scene
        settings = scene.luxcore.sarfis

        # Check halt conditions
        is_halt_enabled, layers_without_halt = utils.is_halt_condition_enabled(scene)
        if not is_halt_enabled:
            msg = "Missing halt condition"
            if layers_without_halt:
                msg += " (on view layers: " + ", ".join(layers_without_halt) + ")"
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        # Make sure file was saved
        blend_filepath = bpy.data.filepath
        if not blend_filepath or bpy.data.is_dirty:
            self.report({"ERROR"}, "Please save the .blend file")
            return {"CANCELLED"}

        # Check if output path is valid
        try:
            output_dir = settings.output_dir
            output_dir_abs = utils.get_abspath(output_dir, must_exist=True, must_be_existing_dir=True)

            test_file_path = os.path.join(output_dir_abs, "__dummyfile__")
            with open(test_file_path, "w") as f:
                f.write("test")
            os.remove(test_file_path)
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        if settings.mode == "single_frame":
            start_frame = end_frame = scene.frame_current
        elif settings.mode == "animation":
            start_frame = scene.frame_start
            end_frame = scene.frame_end
        else:
            raise Exception("Unknown mode")

        print("Starting job for file:", blend_filepath, "Frames:", start_frame, "to", end_frame)
        sarfis.create_job(blend_filepath, start_frame, end_frame)

        sarfis.start_auto_polling()
        return {"FINISHED"}


class LUXCORE_OT_sarfis_pause(bpy.types.Operator):
    bl_idname = "luxcore.sarfis_pause"
    bl_label = "Pause"
    bl_description = ""

    @classmethod
    def poll(self, context):
        return Status.status == Status.RUNNING

    def execute(self, context):
        # Make sure status is up to date
        sarfis.poll_job_details(Status.job_id)
        if self.poll(context):
            sarfis.pause_job(Status.job_id)
        return {"FINISHED"}


class LUXCORE_OT_sarfis_resume(bpy.types.Operator):
    bl_idname = "luxcore.sarfis_resume"
    bl_label = "Resume"
    bl_description = ""

    @classmethod
    def poll(self, context):
        return Status.status == Status.PAUSED

    def execute(self, context):
        # Make sure status is up to date
        sarfis.poll_job_details(Status.job_id)
        if self.poll(context):
            sarfis.queue_job(Status.job_id)
            sarfis.start_auto_polling()
        return {"FINISHED"}


class LUXCORE_OT_sarfis_delete(bpy.types.Operator):
    bl_idname = "luxcore.sarfis_delete"
    bl_label = "Delete"
    bl_description = ""

    @classmethod
    def poll(self, context):
        return Status.status in {Status.PAUSED, Status.ERROR}

    def execute(self, context):
        # Make sure status is up to date
        sarfis.poll_job_details(Status.job_id)
        if self.poll(context):
            sarfis.delete_job(Status.job_id)
            sarfis.start_auto_polling()
        return {"FINISHED"}
