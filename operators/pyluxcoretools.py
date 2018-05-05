import bpy
import os
import platform
from subprocess import Popen, PIPE, run
from shutil import which


class LUXCORE_OT_install_pyside(bpy.types.Operator):
    bl_idname = "luxcore.install_pyside"
    bl_label = "You need PySide. Install it now?"
    bl_description = ""

    def invoke(self, context, event):
        print("invoke")
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        threadcount = context.scene.render.threads
        install_command = 'sudo pip3 install --install-option="--jobs=%d" PySide' % threadcount

        if not which("x-terminal-emulator"):
            self.report({"ERROR"}, "Could not open terminal. Please install PySide by hand:")
            self.report({"ERROR"}, install_command)
            self.report({"ERROR"}, "(You can copy the command from the terminal)")
            print(install_command)
            return {"CANCELLED"}

        script = (
            "'"
            + 'echo "This will install PySide (required by pyluxcoretools UI)";'
            # Show which command will be used to install PySide
            + 'echo "' + install_command.replace('"', '\\"') + '";'
            # Execute the command to install PySide
            + install_command + ';'
            + 'echo "Done. You can close this window now.";'
            # Keep the terminal open
            + 'exec $SHELL'
            + "'"
        )
        run(["x-terminal-emulator", "-e", "bash -c " + script])
        return {"FINISHED"}


class LUXCORE_OT_start_pyluxcoretools(bpy.types.Operator):
    bl_idname = "luxcore.start_pyluxcoretools"
    bl_label = "LuxCore Network Render"
    bl_description = ("Start the pyluxcoretools that can be used to "
                      "start and control network rendering sessions")

    def execute(self, context):
        if platform.system() == "Linux":
            # On Linux, PySide can not be bundled because of this bug:
            # https://github.com/LuxCoreRender/LuxCore/issues/80#issuecomment-378223152
            # So we need to check if PySide is installed, and install it if necessary
            result = run(["pip3", "list"], stdout=PIPE)
            installed_packages = result.stdout.decode()

            if "PySide" not in installed_packages:
                bpy.ops.luxcore.install_pyside("INVOKE_DEFAULT")
                return {"CANCELLED"}

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

        # Set the current working directory to the bin folder so pyluxcore is found
        kwargs.update(cwd=bin_dir)

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
