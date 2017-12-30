import bpy
from .bin import pyluxcore
from .export.image import ImageExporter

# Have to import everything with classes which need to be registered
from . import engine, nodes, operators, properties, ui
from .nodes import materials, volumes, textures
from .ui import config, display, errorlog, halt, light, material, postpro, world

bl_info = {
    "name": "LuxCore",
    "author": "Simon Wendsche (B.Y.O.B.)",
    "version": (2, 0),
    "blender": (2, 77, 0),
    "category": "Render",
    "location": "Info header, render engine menu",
    "description": "LuxCore integration for Blender",
    "warning": "Alpha Version, incomplete",
    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}


def blendluxcore_exit():
    ImageExporter.cleanup()


def register():
    import atexit
    # Make sure we only register the callback once
    atexit.unregister(blendluxcore_exit)
    atexit.register(blendluxcore_exit)

    nodes.materials.register()
    nodes.volumes.register()
    bpy.utils.register_module(__name__)
    ui.register()

    properties.init()

    # Has to be called at least once, can be called multiple times
    pyluxcore.Init()
    print("pyluxcore version:", pyluxcore.Version())


def unregister():
    ui.unregister()
    nodes.materials.unregister()
    nodes.volumes.unregister()
    bpy.utils.unregister_module(__name__)
