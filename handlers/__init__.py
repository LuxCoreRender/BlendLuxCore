import bpy
from bpy.types import SpaceView3D, SpaceImageEditor
from . import (
    draw_imageeditor, exit,
    load_post, scene_update_post,
)


def register():
    import atexit
    # Make sure we only register the callback once
    atexit.unregister(exit.handler)
    atexit.register(exit.handler)

    bpy.app.handlers.load_post.append(load_post.handler)
    bpy.app.handlers.scene_update_post.append(scene_update_post.handler)

    # args = ()
    # draw_imageeditor.handle = SpaceImageEditor.draw_handler_add(draw_imageeditor.handler,
    #                                                             args, 'WINDOW', 'POST_PIXEL')


def unregister():
    bpy.app.handlers.load_post.remove(load_post.handler)
    bpy.app.handlers.scene_update_post.remove(scene_update_post.handler)
    # SpaceImageEditor.draw_handler_remove(draw_imageeditor.handle, 'WINDOW')
