import bpy
from .bin import pyluxcore

bl_info = {
    "name": "BlendLuxCore",
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
    bl_idname = "LUXCORE_RENDER"
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

    bpy.utils.register_class(LuxCoreRenderEngine)

    # RenderEngines also need to tell UI Panels that they are compatible
    # Otherwise most of the UI will be empty when the engine is selected.
    # In this example, we need to see the main render image button and
    # the material preview panel.
    from bl_ui import (
            properties_render,
            properties_material,
            )
    properties_render.RENDER_PT_render.COMPAT_ENGINES.add(LuxCoreRenderEngine.bl_idname)
    properties_material.MATERIAL_PT_preview.COMPAT_ENGINES.add(LuxCoreRenderEngine.bl_idname)


def unregister():
    print("unregister")
    bpy.utils.unregister_class(LuxCoreRenderEngine)

    from bl_ui import (
            properties_render,
            properties_material,
            )
    properties_render.RENDER_PT_render.COMPAT_ENGINES.remove(LuxCoreRenderEngine.bl_idname)
    properties_material.MATERIAL_PT_preview.COMPAT_ENGINES.remove(LuxCoreRenderEngine.bl_idname)


if __name__ == "__main__":
    register()
