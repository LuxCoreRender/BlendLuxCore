from time import time
import math
import bpy
from bpy.types import SpaceView3D
from bgl import *
from ..bin import pyluxcore
from bpy.app.handlers import persistent
from ..export.image import ImageExporter
from .. import utils
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


def luxcore_draw_3dview():
    context = bpy.context
    obj = context.object

    if obj and obj.type == "LAMP" and obj.data.type == "POINT":
        lamp = obj.data
        radius = lamp.luxcore.radius

        if radius > 0:
            x, y, z = obj.location
            steps = 16
            # Optimization
            inv_steps = 1 / steps
            twice_pi = math.pi * 2

            theme = utils.get_theme(context)
            glColor3f(*theme.view_3d.object_active)

            glBegin(GL_LINE_LOOP)
            for i in range(steps):
                glVertex3f(
                    x + (radius * math.cos(i * twice_pi * inv_steps)),
                    y + (radius * math.sin(i * twice_pi * inv_steps)),
                    z
                )
            glEnd()

            glBegin(GL_LINE_LOOP)
            for i in range(steps):
                glVertex3f(
                    x,
                    y + (radius * math.cos(i * twice_pi * inv_steps)),
                    z + (radius * math.sin(i * twice_pi * inv_steps))
                )
            glEnd()

            glBegin(GL_LINE_LOOP)
            for i in range(steps):
                glVertex3f(
                    x + (radius * math.cos(i * twice_pi * inv_steps)),
                    y,
                    z + (radius * math.sin(i * twice_pi * inv_steps))
                )
            glEnd()

            # Reset color
            glColor4f(0.0, 0.0, 0.0, 1.0)


luxcore_draw_3dview_handle = None


def register():
    import atexit
    # Make sure we only register the callback once
    atexit.unregister(blendluxcore_exit)
    atexit.register(blendluxcore_exit)

    bpy.app.handlers.load_post.append(luxcore_load_post)
    bpy.app.handlers.scene_update_post.append(luxcore_scene_update_post)

    # args: The arguments for the draw_callback function, in our case no arguments
    args = ()
    global luxcore_draw_3dview_handle
    luxcore_draw_3dview_handle = SpaceView3D.draw_handler_add(luxcore_draw_3dview, args, 'WINDOW', 'POST_VIEW')


def unregister():
    bpy.app.handlers.load_post.remove(luxcore_load_post)
    bpy.app.handlers.scene_update_post.remove(luxcore_scene_update_post)
    bpy.types.SpaceView3D.draw_handler_remove(luxcore_draw_3dview_handle, 'WINDOW')
