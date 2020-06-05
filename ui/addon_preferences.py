from os.path import basename, dirname
from bpy.types import AddonPreferences
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty
from ..ui import icons
from .. import utils
from ..utils.lol import utils as lol_utils


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

    image_node_thumb_default: BoolProperty(
        name="Show Thumbnails by Default", default=True,
        description="Decide wether the thumbnail is visible on new image nodes (changes do not affect existing nodes)"
    )

    global_dir: StringProperty(
        name="Global Files Directory",
        description="Global storage for your assets, will use subdirectories for the contents",
        subtype='DIR_PATH', default=lol_utils.get_default_directory(), update=lol_utils.save_prefs
    )

    project_subdir: StringProperty(
        name="Project Assets Subdirectory", description="where data will be stored for individual projects",
        subtype='DIR_PATH', default="model",
    )
    max_assetbar_rows: IntProperty(name="Max Assetbar Rows", description="max rows of assetbar in the 3d view",
                                   default=1, min=0, max=20)
    thumb_size: IntProperty(name="Assetbar Thumbnail Size", default=96, min=-1, max=256)
    use_library: BoolProperty(name="Use LuxCore Online Library", default=True)

    def draw(self, context):
        layout = self.layout
        
        if utils.is_cuda_build():
            row = layout.row()
            row.label(text="GPU API:")
            row.prop(self, "gpu_backend", expand=True)

        row = layout.row()
        row.label(text="Image Nodes:")
        row = row.row()
        row.alignment = "LEFT"
        row.prop(self, "image_node_thumb_default")

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

        layout.separator()
        col = layout.column()
        col.label(text="LuxCore Online Library (LOL) Preferences:")
        col = layout.column()

        col.prop(self, "use_library")
        if self.use_library:
            col.prop(self, "global_dir")
            col.prop(self, "project_subdir")
            col.prop(self, "thumb_size")
