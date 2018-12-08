import bpy
from bpy.app.handlers import persistent
from ..bin import pyluxcore
from ..utils import compatibility, find_optix_denoiser


@persistent
def handler(_):
    """ Note: the only argument Blender passes is always None """

    for scene in bpy.data.scenes:
        # Update OpenCL devices if .blend is opened on
        # a different computer than it was saved on
        scene.luxcore.opencl.update_devices_if_necessary()

        if pyluxcore.GetPlatformDesc().Get("compile.LUXRAYS_DISABLE_OPENCL").GetBool():
            # OpenCL not available, make sure we are using CPU device
            scene.luxcore.config.device = "CPU"

        for layer in scene.render.layers:
            # Disable depth pass by default
            if not layer.luxcore.aovs.depth:
                layer.use_pass_z = False

        # Use Blender output path for filesaver by default
        if not scene.luxcore.config.filesaver_path:
            scene.luxcore.config.filesaver_path = scene.render.filepath

        # Try to find optix binary automatically
        find_optix_denoiser(scene)

    # Run converters for backwards compatibility
    compatibility.run()

