import bpy
import subprocess
import os
import platform


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

        env = os.environ.copy()

        if platform.system() == "Linux":
            env["LD_LIBRARY_PATH"] = os.path.dirname(bin_dir)

            zip_path = os.path.join(bin_dir, "pyluxcoretools.zip")
            command = ["python3", zip_path]
        elif platform.system() == "Windows":
            exe_path = os.path.join(bin_dir, "pyluxcoretool.exe")
            command = exe_path
        else:
            raise NotImplementedError("Unsupported system: " + platform.system())

        # - cwd specifies the current working directory
        # - preexec_fn=os.setsid detaches the process from our process group
        #   so it is not ended by Ctrl+C etc. to the parent process
        subprocess.Popen(command, cwd=bin_dir, preexec_fn=os.setsid)
        return {"FINISHED"}
