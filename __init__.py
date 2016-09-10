import bpy
from .bin import pyluxcore

bl_info = {
    "name": "LuxCore",
    "author": "Simon Wendsche (B.Y.O.B.)",
    "version": (1, 7),
    "blender": (2, 77, 0),
    "category": "Render",
    "location": "Info header, render engine menu",
    "description": "LuxCore integration for Blender",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}


class LuxCoreRenderEngine(bpy.types.RenderEngine):
    bl_idname = "LUXCORE"
    bl_label = "LuxCore"
    bl_use_preview = False  # TODO: disabled for now
    bl_use_shading_nodes_custom = True

    def __init__(self):
        print("init")

    def __del__(self):
        # Note: this method is also called when unregister() is called
        print("del")

    def update(self, data, scene):
        """Export scene data for render"""
        print("update")

    def render(self, scene):
        print("render")

    def view_update(self, context):
        print("view_update")

    def view_draw(self, context):
        print("view_draw")


def register():
    print("register")

    pyluxcore.Init()
    print("pyluxcore version", pyluxcore.Version())

    from . import ui
    ui.register()
    bpy.utils.register_class(LuxCoreRenderEngine)


def unregister():
    print("unregister")
    from . import ui
    ui.unregister()
    bpy.utils.unregister_class(LuxCoreRenderEngine)
