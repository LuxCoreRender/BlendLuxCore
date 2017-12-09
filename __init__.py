import bpy

# Have to import everything with classes which need to be registered
from . import engine, nodes, operators, properties, ui
from .nodes import materials
from .ui import config, material

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


def register():
    ui.register()
    nodes.materials.register()
    bpy.utils.register_module(__name__, verbose=True)

    properties.init()


def unregister():
    ui.unregister()
    nodes.materials.unregister()
    bpy.utils.unregister_module(__name__)
