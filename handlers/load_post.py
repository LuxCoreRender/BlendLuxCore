import os
import tempfile
import bpy
from bpy.app.handlers import persistent
from ..bin import pyluxcore
from .. import utils
from ..utils import compatibility


@persistent
def handler(_):
    """ Note: the only argument Blender passes is always None """

    for scene in bpy.data.scenes:
        # Update OpenCL devices if .blend is opened on
        # a different computer than it was saved on
        updated = scene.luxcore.opencl.update_devices_if_necessary()

        if updated:
            # Set first GPU as film OpenCL device, or disable film OpenCL if no GPUs found
            scene.luxcore.config.film_opencl_enable = False
            scene.luxcore.config.film_opencl_device = "none"
            for i, device in enumerate(scene.luxcore.opencl.devices):
                if device.type == "OPENCL_GPU":
                    scene.luxcore.config.film_opencl_device = str(i)
                    scene.luxcore.config.film_opencl_enable = True
                    break

        if pyluxcore.GetPlatformDesc().Get("compile.LUXRAYS_DISABLE_OPENCL").GetBool():
            # OpenCL not available, make sure we are using CPU device
            scene.luxcore.config.device = "CPU"

        # Use Blender output path for filesaver by default
        if not scene.luxcore.config.filesaver_path:
            scene.luxcore.config.filesaver_path = scene.render.filepath

        if not scene.luxcore.config.photongi.file_path:
            blend_name = utils.get_blendfile_name()
            if blend_name:
                pgi_path = "//" + blend_name + ".pgi"
            else:
                # Blend file was not saved yet
                pgi_path = os.path.join(tempfile.gettempdir(), "Untitled.pgi")
            scene.luxcore.config.photongi.file_path = pgi_path

    # Run converters for backwards compatibility
    compatibility.run()
