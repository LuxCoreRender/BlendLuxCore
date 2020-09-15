import bpy
from os.path import basename, dirname
from bpy.types import AddonPreferences
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty
from ..ui import icons
from .. import utils
from ..utils.lol import utils as lol_utils
from ..export.mesh_converter import custom_normals_supported


film_device_items = []


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

    def film_device_items_callback(self, context):
        backend_to_type = {
            "OPENCL": "OPENCL_GPU",
            "CUDA": "CUDA_GPU",
        }

        devices = context.scene.luxcore.devices.devices
        device_type_filter = backend_to_type[self.gpu_backend]
        # Omit Intel GPU devices because they can lead to crashes
        gpu_devices = [(index, device) for (index, device) in enumerate(devices)
                       if (device.type == device_type_filter and not "intel" in device.name.lower())]

        items = [(str(index), f"{device.name} ({self.gpu_backend})", "", i)
                 for i, (index, device) in enumerate(gpu_devices)]
        # The first item in the list is the default, so we append the CPU fallback at the end
        items += [("none", "CPU", "", len(items))]

        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        global film_device_items
        film_device_items = items
        return items

    film_device: EnumProperty(name="Film Device", items=film_device_items_callback,
                              description="Which device to use to compute the imagepipeline")

    use_optix_if_available: BoolProperty(name="Use OptiX if Available", default=True,
                                         description="Use the OptiX backend if possible, to speed up ray/triangle "
                                                     "intersections and BHV building and to save memory. Check the "
                                                     "console when rendering to see if OptiX is actually used. "
                                                     "It usually only makes sense to disable this for benchmark "
                                                     "comparisons between CUDA and OptiX")

    image_node_thumb_default: BoolProperty(
        name="Show Thumbnails by Default", default=True,
        description="Decide wether the thumbnail is visible on new image nodes (changes do not affect existing nodes)"
    )

    # LuxCore online library properties
    global_dir: StringProperty(
        name="Global Files Directory",
        description="Global storage for your assets, will use subdirectories for the contents",
        subtype='DIR_PATH', default=lol_utils.get_default_directory()
    )

    max_assetbar_rows: IntProperty(name="Max Assetbar Rows", description="max rows of assetbar in the 3d view",
                                   default=1, min=0, max=20)
    thumb_size: IntProperty(name="Assetbar Thumbnail Size", default=96, min=-1, max=256)
    use_library: BoolProperty(name="Use LuxCore Online Library", default=True)

    def draw(self, context):
        layout = self.layout
        SPLIT_FACTOR = 1/3
        
        if not custom_normals_supported():
            layout.label(text="No official support for this Blender version!", icon=icons.WARNING)
            layout.label(text="Custom normals will not work, and there might be other problems!", icon=icons.WARNING)

        row = layout.row()
        row.label(text="GPU API:")
        
        if utils.is_cuda_build():
            row.prop(self, "gpu_backend", expand=True)
            
            if self.gpu_backend == "CUDA":
                row = layout.row()
                split = row.split(factor=SPLIT_FACTOR)
                split.label(text="")
                split.prop(self, "use_optix_if_available")
            
            row = layout.row()
            split = row.split(factor=SPLIT_FACTOR)
            split.label(text="Film Device:")
            split.prop(self, "film_device", text="")
        elif utils.is_opencl_build():
            row.label(text="OpenCL")
            
            row = layout.row()
            split = row.split(factor=SPLIT_FACTOR)
            split.label(text="Film Device:")
            split.prop(self, "film_device", text="")
        else:
            row.label(text="Not available in this build")
        
        row = layout.row()
        split = row.split(factor=SPLIT_FACTOR)
        split.label(text="Image Nodes:")
        split.prop(self, "image_node_thumb_default")

        row = layout.row()
        row.label(text="Community:")
        op = row.operator("luxcore.open_website", text="Forums", icon=icons.URL)
        op.url = "https://forums.luxcorerender.org/"
        op = row.operator("luxcore.open_website", text="Discord", icon=icons.URL)
        op.url = "https://discord.gg/chPGsKV"

        row = layout.row()
        row.label(text="Download:")
        op = row.operator("luxcore.open_website", text="BlendLuxCore Releases", icon=icons.URL)
        op.url = "https://github.com/LuxCoreRender/BlendLuxCore/releases"
        row.label(text="")

        layout.separator()
        col = layout.column()
        col.label(text="LuxCore Online Library (LOL) Preferences:")
        col = layout.column()

        col.prop(self, "use_library")
        if self.use_library:
            col.prop(self, "global_dir")
            col.prop(self, "thumb_size")
