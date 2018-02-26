import bpy
from .bin import pyluxcore

# Have to import everything with classes which need to be registered
from . import engine, handlers, nodes, operators, properties, ui
from .nodes import materials, volumes, textures
from .ui import (
    aovs, blender_object, camera, config, display, errorlog,
    halt, light, material, mesh, particle, postpro, render_layer,
    texture, world
)
from .handlers import blendluxcore_exit, luxcore_load_post, luxcore_scene_update_post

bl_info = {
    "name": "LuxCore",
    "author": "Simon Wendsche (B.Y.O.B.), Michael Klemm (neo2068), Philstix",
    "version": (2, 0),
    "blender": (2, 79, 0),
    "category": "Render",
    "location": "Info header, render engine menu",
    "description": "LuxCore integration for Blender",
    "warning": "alpha5",
    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}


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
