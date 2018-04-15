import bpy
import os
import platform
from subprocess import Popen, PIPE


class LUXCORE_OT_start_pyluxcoretools(bpy.types.Operator):
    bl_idname = "luxcore.start_pyluxcoretools"
    bl_label = "LuxCore Network Render"
    bl_description = ("Start the pyluxcoretools that can be used to "
                      "start and control network rendering sessions")

    def execute(self, context):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        # Call dirname once to go up 1 level (from BlendLuxCore/operators/)
        blendluxcore_dir = os.path.dirname(current_dir)
        bin_dir = os.path.join(blendluxcore_dir, "bin")

        # Set system/version dependent "start_new_session" analogs.
        # This ensures that the pyluxcoretools process is not stopped
        # when the parent process (Blender) is stopped.
        # Adapted from https://stackoverflow.com/a/13256908
        kwargs = {}
        if platform.system() == "Windows":
            CREATE_NEW_PROCESS_GROUP = 0x00000200  # note: could get it from subprocess
            DETACHED_PROCESS = 0x00000008  # 0x8 | 0x200 == 0x208
            kwargs.update(creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        else:
            kwargs.update(start_new_session=True)

        if platform.system() == "Linux":
            zip_path = os.path.join(bin_dir, "pyluxcoretools.zip")
            command = ["python3", zip_path]
        elif platform.system() == "Windows":
            exe_path = os.path.join(bin_dir, "pyluxcoretool.exe")
            command = exe_path
        else:
            raise NotImplementedError("Unsupported system: " + platform.system())

        Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, **kwargs)

        return {"FINISHED"}
