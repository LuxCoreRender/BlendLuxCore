import bpy
from bpy.app.handlers import persistent
from .bin import pyluxcore
from .export.image import ImageExporter
from .utils import compatibility

# Have to import everything with classes which need to be registered
from . import engine, nodes, operators, properties, ui
from .nodes import materials, volumes, textures
from .ui import (blender_object, camera, config, display, errorlog,
                 halt, light, material, mesh, particle, postpro, texture, world)

bl_info = {
    "name": "LuxCore",
    "author": "Simon Wendsche (B.Y.O.B.), Michael Klemm (neo2068)",
    "version": (2, 0),
    "blender": (2, 79, 0),
    "category": "Render",
    "location": "Info header, render engine menu",
    "description": "LuxCore integration for Blender",
    "warning": "alpha4",
    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}


def blendluxcore_exit():
    ImageExporter.cleanup()


@persistent
def luxcore_load_post(_):
    """ Note: the only argument Blender passes is always None """

    # Update OpenCL devices if .blend is opened on a different computer than it was saved on
    for scene in bpy.data.scenes:
        scene.luxcore.opencl.update_devices_if_necessary()

        if pyluxcore.GetPlatformDesc().Get("compile.LUXRAYS_DISABLE_OPENCL").GetBool():
            # OpenCL not available, make sure we are using CPU device
            scene.luxcore.config.device = "CPU"

    # Run converters for backwards compatibility
    compatibility.run()


@persistent
def luxcore_scene_update_post(scene):
    for mat in bpy.data.materials:
        node_tree = mat.luxcore.node_tree

        if node_tree and node_tree.name != mat.name:
            node_tree.name = mat.name


def register():
    import atexit
    # Make sure we only register the callback once
    atexit.unregister(blendluxcore_exit)
    atexit.register(blendluxcore_exit)

    bpy.app.handlers.load_post.append(luxcore_load_post)
    bpy.app.handlers.scene_update_post.append(luxcore_scene_update_post)

    nodes.materials.register()
    nodes.textures.register()
    nodes.volumes.register()
    bpy.utils.register_module(__name__)
    ui.register()

    properties.init()

    # Has to be called at least once, can be called multiple times
    pyluxcore.Init()
    print("pyluxcore version:", pyluxcore.Version())


def unregister():
    bpy.app.handlers.load_post.remove(luxcore_load_post)
    bpy.app.handlers.scene_update_post.remove(luxcore_scene_update_post)

    ui.unregister()
    nodes.materials.unregister()
    nodes.textures.unregister()
    nodes.volumes.unregister()
    bpy.utils.unregister_module(__name__)
