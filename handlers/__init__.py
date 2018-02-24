from time import time
import bpy
from ..bin import pyluxcore
from bpy.app.handlers import persistent
from ..export.image import ImageExporter
from ..utils import compatibility


def blendluxcore_exit():
    ImageExporter.cleanup()


@persistent
def luxcore_load_post(_):
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

    # Run converters for backwards compatibility
    compatibility.run()


# We only sync material and node tree names every second to reduce CPU load
NAME_UPDATE_INTERVAL = 1  # seconds
last_name_update = time()

@persistent
def luxcore_scene_update_post(scene):
    global last_name_update
    if time() - last_name_update < NAME_UPDATE_INTERVAL:
        return
    last_name_update = time()

    # If material name was changed, rename the node tree, too.
    # Note that bpy.data.materials.is_updated is always False here
    # so we can't use it as fast check.
    for mat in bpy.data.materials:
        node_tree = mat.luxcore.node_tree

        if node_tree and node_tree.name != mat.name:
            node_tree.name = mat.name
