import bpy
from bpy.app.handlers import persistent
from .bin import pyluxcore
from .export.image import ImageExporter

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
    "warning": "alpha2",
    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}


def blendluxcore_exit():
    ImageExporter.cleanup()


@persistent
def blendluxcore_scene_update_post(scene):
    for mat in bpy.data.materials:
        node_tree = mat.luxcore.node_tree

        if node_tree and node_tree.name != mat.name:
            node_tree.name = mat.name


def register():
    import atexit
    # Make sure we only register the callback once
    atexit.unregister(blendluxcore_exit)
    atexit.register(blendluxcore_exit)

    bpy.app.handlers.scene_update_post.append(blendluxcore_scene_update_post)

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
    bpy.app.handlers.scene_update_post.remove(blendluxcore_scene_update_post)

    ui.unregister()
    nodes.materials.unregister()
    nodes.textures.unregister()
    nodes.volumes.unregister()
    bpy.utils.unregister_module(__name__)
