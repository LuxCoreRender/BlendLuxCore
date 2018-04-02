import bpy
from .bin import pyluxcore

# Have to import everything with classes which need to be registered
from . import engine, handlers, nodes, operators, properties, ui
from .nodes import materials, volumes, textures
from .ui import (
    aovs, blender_object, camera, config, display, errorlog,
    halt, light, lightgroups, material, mesh, particle, postpro,
    render_layer, texture, world
)

bl_info = {
    "name": "LuxCore",
    "author": "Simon Wendsche (B.Y.O.B.), Michael Klemm (neo2068), Philstix",
    "version": (2, 0),
    "blender": (2, 79, 0),
    "category": "Render",
    "location": "Info header, render engine menu",
    "description": "LuxCore integration for Blender",
    "warning": "beta1",
    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}


def register():
    handlers.register()
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
    handlers.unregister()
    ui.unregister()
    nodes.materials.unregister()
    nodes.textures.unregister()
    nodes.volumes.unregister()
    bpy.utils.unregister_module(__name__)
