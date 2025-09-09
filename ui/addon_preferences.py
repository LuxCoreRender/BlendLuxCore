"""Addon Preferences user interface."""

from importlib.metadata import version

_needs_reload = "bpy" in locals()

import bpy
from bpy.types import AddonPreferences
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty

from .. import ui
from ..ui import icons
from .. import utils
from ..utils import luxutils
from ..utils.lol import utils as lol_utils


if _needs_reload:
    import importlib

    ui = importlib.reload(ui)
    utils = importlib.reload(utils)
    luxutils = importlib.reload(luxutils)
    lol_utils = importlib.reload(lol_utils)


SPLIT_FACTOR = 1 / 3

film_device_items = []

enum_wheel_sources = (
    (
        "PyPI",
        "PyPI (default)",
        "Get PyLuxCore from Python Package Index (PyPI)",
    ),
    (
        "LocalWheel",
        "Local Wheel",
        "Get PyLuxCore from a local wheel file, not including dependencies",
    ),
    (
        "LocalFolder",
        "Local Wheel + dependencies",
        "Get PyLuxCore from a local folder, containing PyLuxCore wheel "
        "and all its dependencies",
    ),
)


class LuxCoreAddonPreferences(AddonPreferences):
    """Addon Preference panel."""

    # id name for 4.2
    bl_idname = utils.get_module_name()

    gpu_backend_items = [
        ("OPENCL", "OpenCL", "Use OpenCL for GPU acceleration", 0),
        (
            "CUDA",
            "CUDA/OptiX",
            "Use CUDA/OptiX for GPU acceleration. "
            "OptiX acceleration is used only when supported hardware is detected",
            1,
        ),
    ]
    gpu_backend: EnumProperty(items=gpu_backend_items, default="OPENCL")

    def film_device_items_callback(self, context):
        """List items for Film Device property (callback)."""
        backend_to_type = {
            "OPENCL": "OPENCL_GPU",
            "CUDA": "CUDA_GPU",
        }

        devices = context.scene.luxcore.devices.devices
        device_type_filter = backend_to_type[self.gpu_backend]
        # Omit Intel GPU devices because they can lead to crashes
        gpu_devices = [
            (index, device)
            for (index, device) in enumerate(devices)
            if (
                device.type == device_type_filter
                and not "intel" in device.name.lower()
            )
        ]

        items = [
            (str(index), f"{device.name} ({self.gpu_backend})", "", i)
            for i, (index, device) in enumerate(gpu_devices)
        ]
        # The first item in the list is the default, so we append the CPU
        # fallback at the end
        items += [("none", "CPU", "", len(items))]

        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        global film_device_items
        film_device_items = items
        return items

    film_device: EnumProperty(
        name="Film Device",
        items=film_device_items_callback,
        description="Which device to use to compute the imagepipeline",
    )

    image_node_thumb_default: BoolProperty(
        name="Show Thumbnails by Default",
        default=True,
        description=(
            "Decide wether the thumbnail is visible on new image nodes "
            "(changes do not affect existing nodes)"
        ),
    )

    # LuxCore online library properties
    global_dir: StringProperty(
        name="Global Files Directory",
        description=(
            "Global storage for your assets, "
            "will use subdirectories for the contents"
        ),
        subtype="DIR_PATH",
        default=lol_utils.get_default_directory(),
    )
    lol_host: StringProperty(
        name="Host URL",
        description="Address of the LuxCore Online Library server",
        default="https://luxcorerender.org/lol",
    )
    lol_http_host: StringProperty(
        name="HTTP Host",
        description=(
            " FOR DEVELOPERS ONLY! DO NOT EDIT! "
            "Hostname transferred with HTTP(s) request. Needed for technical reasons."
        ),
        default="www.luxcorerender.org",
    )
    lol_version: StringProperty(
        name="Library Version",
        description="Version of the LuxCore Online Library.",
        default="v2.5",
    )
    lol_useragent: StringProperty(
        name="HTTP User-Agent",
        description="User Agent transmitted with requests",
        default=f"BlendLuxCore/{utils.get_version_string()}",
    )

    max_assetbar_rows: IntProperty(
        name="Max Assetbar Rows",
        description="max rows of assetbar in the 3d view",
        default=1,
        min=0,
        max=20,
    )
    thumb_size: IntProperty(
        name="Assetbar Thumbnail Size", default=96, min=-1, max=256
    )
    use_library: BoolProperty(name="Use LuxCore Online Library", default=True)

    display_luxcore_logs: BoolProperty(name="Show LuxCore Logs", default=True)

    show_advanced_settings: BoolProperty(
        name="Use Advanced Settings",
        description=(
            "Development and Debugging settings."
            "WARNING! May cause BlendLuxCore to become unusable. "
            "Do not modify unless you know what you are doing"
        ),
        default=False,
    )

    wheel_source: bpy.props.EnumProperty(
        name="Source",
        description="PyLuxCore source",
        items=enum_wheel_sources,
        default="PyPI",
    )

    path_to_wheel: bpy.props.StringProperty(
        name="Path to File",
        description="Path to PyLuxCore Wheel file",
        subtype="FILE_PATH",
    )

    path_to_folder: bpy.props.StringProperty(
        name="Path to Folder",
        description="Path to Folder containing PyLuxCore Wheel + the other dependencies",
        subtype="DIR_PATH",
    )

    reinstall_upon_reloading: bpy.props.BoolProperty(
        name="Reinstall upon reloading",
        description="Reinstall every time BlendLuxCore is reloaded",
    )

    # Read-only string property, returns the current date
    def get_pyluxcore_version(self):
        """Provide pyluxcore version."""
        try:
            pyluxcore_version = version("pyluxcore")
        except ModuleNotFoundError:
            pyluxcore_version = "ERROR: could not find pyluxcore"
        return pyluxcore_version

    pyluxcore_version: StringProperty(name="", get=get_pyluxcore_version)

    def _draw_general(self):
        """Draw general settings."""

        layout = self.layout

        row = layout.row()
        row.label(text="General settings:")

        row = layout.row()
        row.label(text="GPU API:")

        if utils.luxutils.is_cuda_build():
            row.prop(self, "gpu_backend", expand=True)

            row = layout.row()
            split = row.split(factor=SPLIT_FACTOR)
            split.label(text="Film Device:")
            split.prop(self, "film_device", text="")
        elif utils.luxutils.is_opencl_build():
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
        op = row.operator(
            "luxcore.open_website", text="Forums", icon=icons.URL
        )
        op.url = "https://forums.luxcorerender.org/"
        op = row.operator(
            "luxcore.open_website", text="Discord", icon=icons.URL
        )
        op.url = "https://discord.gg/chPGsKV"

        row = layout.row()
        row.label(text="Download:")
        op = row.operator(
            "luxcore.open_website",
            text="BlendLuxCore Releases",
            icon=icons.URL,
        )
        op.url = "https://github.com/LuxCoreRender/BlendLuxCore/releases"
        row.label(text="")

        # LuxCore logging
        row = layout.row()
        split = row.split(factor=SPLIT_FACTOR)
        split.label(text="LuxCore Logs:")
        split.prop(self, "display_luxcore_logs")

        # pyluxcore version
        row = layout.row()
        split = row.split(factor=SPLIT_FACTOR)
        split.label(text="Pyluxcore version:")
        split.prop(self, "pyluxcore_version")

        # Final separator (keep at the end)
        layout.separator()

    def _draw_lol(self):
        """Draw LuxCore Online Library (lol)."""

        layout = self.layout

        row = layout.row()
        split = row.split(factor=SPLIT_FACTOR)
        split.label(text="LuxCore Online Library (LOL):")
        split.prop(self, "use_library")

        if self.use_library:
            row = layout.row()
            split = row.split(factor=SPLIT_FACTOR)
            split.label(text="Global Files Directory:")
            split.prop(self, "global_dir", text="")

            row = layout.row()
            split = row.split(factor=SPLIT_FACTOR)
            split.label(text="Host URL:")
            split.prop(self, "lol_host", text="")

            row = layout.row()
            split = row.split(factor=SPLIT_FACTOR)
            split.label(text="HTTP Host:")
            split.prop(self, "lol_http_host", text="")

            row = layout.row()
            split = row.split(factor=SPLIT_FACTOR)
            split.label(text="Thumb Size:")
            split.prop(self, "thumb_size", text="")

        layout.separator()

    def _draw_advanced(self):
        """Draw advanced settings panel."""
        layout = self.layout

        row = layout.row()
        split = row.split(factor=SPLIT_FACTOR)
        split.label(text="Advanced Settings:")
        split.prop(self, "show_advanced_settings")

        if self.show_advanced_settings:
            col = layout.row()
            col.label(
                text=(
                    "WARNING! THE FOLLOWING SETTINGS MAY CAUSE BLENDLUXCORE "
                    "TO BECOME UNUSABLE. "
                    "*** DO NOT MODIFY UNLESS YOU KNOW WHAT YOU ARE DOING. ***"
                )
            )
            # Source selector
            row = layout.row()
            split = row.split(factor=SPLIT_FACTOR)
            split.label(text="Wheel source:")
            split.prop(self, "wheel_source", expand=False, text="")

            if self.wheel_source == "PyPI":
                pass
            elif self.wheel_source == "LocalWheel":
                # File
                row = layout.row()
                split = row.split(factor=SPLIT_FACTOR)
                split.label(text="Path to File:")
                split.prop(self, "path_to_wheel", text="")
            elif self.wheel_source == "LocalFolder":
                # Folder
                row = layout.row()
                split = row.split(factor=SPLIT_FACTOR)
                split.label(text="Path to Folder:")
                split.prop(self, "path_to_folder", text="")
            else:
                raise RuntimeError(f"Unhandled wheel source: {wheel_source}")

            row = layout.row()
            row.prop(self, "reinstall_upon_reloading")

    def draw(self, context):
        """Draw addon preferences panel (callback)."""

        # General settings
        self._draw_general()

        # LuxCore Online Library
        self._draw_lol()

        # Advanced settings panel
        self._draw_advanced()
