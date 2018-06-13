from .. import export
from ..draw.viewport import FrameBuffer
from ..utils import render as utils_render


def view_update(engine, context, changes=None):
    scene = context.scene
    print("[Engine/Viewport] view_update")

    scene.luxcore.errorlog.clear()

    if engine.session is None:
        print("[Engine/Viewport] New session")
        try:
            engine.update_stats("Creating Render Session...", "")
            engine.exporter = export.Exporter(scene)
            # Note: in viewport render, the user can't cancel the
            # export (Blender limitation), so we don't pass engine here
            engine.session = engine.exporter.create_session(context)
            engine.session.Start()
            return
        except Exception as error:
            del engine.session
            engine.session = None
            # Reset the exporter to invalidate all caches
            engine.exporter = export.Exporter(scene)

            engine.update_stats("Error: ", str(error))
            scene.luxcore.errorlog.add_error(error)

            import traceback
            traceback.print_exc()
            return

    if changes is None:
        changes = engine.exporter.get_changes(context)

    if changes & export.Change.CONFIG:
        # Film resize requires a new framebuffer
        engine.framebuffer = FrameBuffer(context)

    # We have to re-assign the session because it might have been replaced due to filmsize change
    engine.session = engine.exporter.update(context, engine.session, changes)
    

def view_draw(engine, context):
    scene = context.scene

    # Check for changes because some actions in Blender (e.g. moving the viewport
    # camera) do not trigger a view_update() call, but only a view_draw() call.
    changes = engine.exporter.get_changes(context)

    if changes & export.Change.REQUIRES_VIEW_UPDATE:
        engine.tag_redraw()
        view_update(engine, context, changes)
        return
    elif changes & export.Change.CAMERA:
        # Only update in view_draw if it is a camera update,
        # for everything else we call view_update().
        # We have to re-assign the session because it might have been
        # replaced due to filmsize change.
        engine.session = engine.exporter.update(context, engine.session, export.Change.CAMERA)

    # On startup we don't have a framebuffer yet
    if engine.framebuffer is None:
        engine.framebuffer = FrameBuffer(context)

    # Update and draw the framebuffer
    try:
        engine.session.UpdateStats()
    except RuntimeError as error:
        print("[Engine/Viewport] Error during UpdateStats():", error)
    engine.session.WaitNewFrame()
    engine.framebuffer.update(engine.session)

    region_size = context.region.width, context.region.height
    view_camera_offset = list(context.region_data.view_camera_offset)
    view_camera_zoom = context.region_data.view_camera_zoom
    engine.framebuffer.draw(region_size, view_camera_offset, view_camera_zoom, engine, context)

    # Check if we need to pause the viewport render
    stats = engine.session.GetStats()
    rendered_time = stats.Get("stats.renderengine.time").GetFloat()
    halt_time = scene.luxcore.viewport.halt_time
    status_message = "%d/%ds" % (rendered_time, halt_time)

    if rendered_time > halt_time:
        if not engine.session.IsInPause():
            print("[Engine/Viewport] Pausing session")
            engine.session.Pause()
        status_message += " (Paused)"
    else:
        # Not in pause yet, keep drawing
        engine.tag_redraw()

    # Show formatted statistics in Blender UI
    config = engine.session.GetRenderConfig()
    pretty_stats = utils_render.get_pretty_stats(config, stats, scene, context)
    engine.update_stats(pretty_stats, status_message)
