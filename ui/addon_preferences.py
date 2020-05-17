from os.path import basename, dirname
from bpy.types import AddonPreferences
from bpy.props import EnumProperty
from ..ui import icons
from .. import utils


class LuxCoreAddonPreferences(AddonPreferences):
    # Must be the addon directory name
    # (by default "BlendLuxCore", but a user/dev might change the folder name)
    # We use dirname() two times to go up one level in the file system
    bl_idname = basename(dirname(dirname(__file__)))

    gpu_backend_items = [
        ("OPENCL", "OpenCL", "Use OpenCL for GPU acceleration", 0),
        ("CUDA", "CUDA", "Use CUDA for GPU acceleration", 1),
    ]
    gpu_backend: EnumProperty(items=gpu_backend_items, default="OPENCL")

    def draw(self, context):
        layout = self.layout
        
        if utils.is_cuda_build():
            row = layout.row()
            row.label(text="GPU API:")
            row.prop(self, "gpu_backend", expand=True)

        row = layout.row()
        row.label(text="Update or downgrade:")
        row.operator("luxcore.change_version", icon=icons.DOWNLOAD)
        # Add empty space to the right of the button
        row.label(text="")

        row = layout.row()
        row.label(text="Community:")
        op = row.operator("luxcore.open_website", text="Forums", icon=icons.URL)
        op.url = "https://forums.luxcorerender.org/"
        op = row.operator("luxcore.open_website", text="Discord", icon=icons.URL)
        op.url = "https://discord.gg/chPGsKV"
