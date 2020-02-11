import bpy
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
        # TODO: once user-selectable filepath is implemented, check here if we can create a testfile in the
        #  output directory and throw an error if not (to prevent problems later when the results are retrieved)

        filepath = bpy.data.filepath

        print("Starting job for file:", filepath)
        sarfis.create_job(filepath)

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
        sarfis.poll_job_status(Status.job_id)
        if self.poll(context):
            sarfis.pause_job(Status.job_id)
        return {"FINISHED"}


class LUXCORE_OT_sarfis_resume(bpy.types.Operator):
    bl_idname = "luxcore.sarfis_resume"
    bl_label = "Pause"
    bl_description = ""

    @classmethod
    def poll(self, context):
        return Status.status == Status.PAUSED

    def execute(self, context):
        # Make sure status is up to date
        sarfis.poll_job_status(Status.job_id)
        if self.poll(context):
            sarfis.queue_job(Status.job_id)
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
        sarfis.poll_job_status(Status.job_id)
        if self.poll(context):
            sarfis.delete_job(Status.job_id)
        return {"FINISHED"}
