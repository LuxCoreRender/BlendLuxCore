_needs_reload = "bpy" in locals()

import bpy

from bpy.types import SpaceView3D, SpaceImageEditor

from . import (
    depsgraph_update_post, draw_imageeditor,
    exit, frame_change_pre, load_post,
)

if _needs_reload:
    import importlib
    modules = (
        depsgraph_update_post,
        draw_imageeditor,
        exit,
        frame_change_pre,
        load_post,
    )
    for module in modules:
        importlib.reload(module)


def register():
    import atexit
    # Make sure we only register the callback once
    atexit.unregister(exit.handler)
    atexit.register(exit.handler)

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post.handler)
    bpy.app.handlers.frame_change_pre.append(frame_change_pre.handler)
    bpy.app.handlers.load_post.append(load_post.handler)

    args = ()
    draw_imageeditor.handle = SpaceImageEditor.draw_handler_add(draw_imageeditor.handler,
                                                                args, 'WINDOW', 'POST_PIXEL')


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post.handler)
    bpy.app.handlers.frame_change_pre.remove(frame_change_pre.handler)
    bpy.app.handlers.load_post.remove(load_post.handler)
    SpaceImageEditor.draw_handler_remove(draw_imageeditor.handle, 'WINDOW')
