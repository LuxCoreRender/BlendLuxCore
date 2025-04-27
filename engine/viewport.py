from time import time
import bpy
import pyluxcore
from .. import export
from ..draw.viewport import FrameBuffer
from .. import utils
from ..utils import render as utils_render
from ..utils import get_addon_preferences
from ..utils.log import LuxCoreLog
from ..utils.errorlog import LuxCoreErrorLog
from ..export.config import convert_viewport_engine

# Executed in separate thread
def start_session(engine):
    try:
        engine.session.Start()
        engine.viewport_start_time = time()
    except ReferenceError:
        # Could not start render session because RenderEngine struct was deleted (caused
        # by the user cancelling the viewport render before this function is called)
        return
    except Exception as error:
        engine.session = None
        # Reset the exporter to invalidate all caches
        engine.exporter = None

        engine.update_stats("Error: ", str(error))
        LuxCoreErrorLog.add_error(error)

        import traceback
        traceback.print_exc()

    # Note: Due to CPython implementation details, it's not necessary to use a lock here (this modification is atomic)
    engine.starting_session = False

def force_session_restart(engine):
    """
    https://github.com/LuxCoreRender/BlendLuxCore/issues/577
    For unknown reasons, the old way of handling changes to the renderconfig, like a viewport resize
    or renderengine settings edit, now causes a memory leak. I have not been able to track it down.
    (The original code is in export/__init__.py in the method _update_config())
    As a workaround, I stop and delete the session to trigger a full re-export of the scene and
    a fresh restart of the viewport render.
    """
    if engine.session is not None:
        engine.session.Stop()
        engine.session = None

def view_update(engine, context, depsgraph, changes=None):
    start = time()

    if engine.starting_session or engine.viewport_fatal_error:
        # Prevent deadlock
        return

    LuxCoreErrorLog.clear(force_ui_update=False)

    if engine.session is None:
        if not engine.viewport_starting_message_shown:
            # Let one engine.view_draw() happen so it shows a message in the UI
            return

        if not engine.is_first_viewport_start:
            filmsize = utils.calc_filmsize(depsgraph.scene_eval, context)
            was_resized = engine.last_viewport_size != filmsize
            engine.last_viewport_size = filmsize

            if was_resized:
                engine.time_of_last_viewport_resize = time()
                return
            elif time() - engine.time_of_last_viewport_resize < engine.VIEWPORT_RESIZE_TIMEOUT:
                # Don't re-export the session before the timeout is done, to prevent constant re-exports while resizing
                return
        else:
            display_luxcore_logs = get_addon_preferences(bpy.context).display_luxcore_logs
            if display_luxcore_logs:
                pyluxcore.SetLogHandler(LuxCoreLog.add)
            else:
                pyluxcore.SetLogHandler(LuxCoreLog.silent)


        try:
            print("=" * 50)
            print("[Engine/Viewport] New session")
            engine.exporter = export.Exporter()
            engine.session = engine.exporter.create_session(depsgraph, context, engine=engine)
            # Start in separate thread to avoid blocking the UI
            engine.starting_session = True
            engine.is_first_viewport_start = False
            import _thread
            _thread.start_new_thread(start_session, (engine,))
        except Exception as error:
            if engine.session is not None:
                # in case engine.session was already set in the try block before the error
                del engine.session
            engine.session = None
            # Reset the exporter to invalidate all caches
            engine.exporter = None
            engine.viewport_fatal_error = str(error)

            engine.update_stats("Error: ", str(error))
            LuxCoreErrorLog.add_error(error)

            import traceback
            traceback.print_exc()
        return

    s = time()
    changes = engine.exporter.get_changes(depsgraph, context, changes)
    delta_t = (time() - s) * 1000
    print(f"[BLC] view_update(): checking for other changes took {delta_t:.1f} ms")

    if changes:
        if changes & export.Change.REQUIRES_VIEW_UPDATE:
            # Only restart the session if the view transform didn't change by itself
            force_session_restart(engine)
            return
        s = time()
        # We have to re-assign the session because it might have been replaced due to filmsize change
        engine.session = engine.exporter.update(depsgraph, context, engine.session, changes)
        engine.viewport_start_time = time()

        if engine.framebuffer:
            engine.framebuffer.reset_denoiser()
        delta_t = (time() - s) * 1000
        print(f"[BLC] view_update(): applying changes took {delta_t:.1f} ms")

    delta_t = (time() - start) * 1000
    print(f"[BLC] view_update() took {delta_t:.1f} ms")


def view_draw(engine, context, depsgraph):
    scene = depsgraph.scene_eval

    if engine.starting_session:
        engine.tag_redraw()
        return

    if engine.viewport_fatal_error:
        engine.update_stats("Error:", engine.viewport_fatal_error)
        engine.tag_redraw()
        return

    if engine.session is None:
        config = scene.luxcore.config
        definitions = {}
        luxcore_engine, _ = convert_viewport_engine(context, scene, definitions, config)
        message = ""

        if luxcore_engine.endswith("OCL"):
            # Create dummy renderconfig to check if we have to compile OpenCL kernels
            luxcore_scene = pyluxcore.Scene()
            definitions = {
                "scene.camera.type": "perspective",
            }
            luxcore_scene.Parse(utils.create_props("", definitions))

            devices = scene.luxcore.devices
            definitions = {
                "renderengine.type": "RTPATHOCL",
                "sampler.type": "TILEPATHSAMPLER",
                "scene.epsilon.min": config.min_epsilon,
                "scene.epsilon.max": config.max_epsilon,
                "opencl.devices.select": devices.devices_to_selection_string(),
            }
            config_props = utils.create_props("", definitions)
            renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)

            if not renderconfig.HasCachedKernels():
                gpu_backend = utils.get_addon_preferences(context).gpu_backend
                message = f"Compiling {gpu_backend} kernels (just once, usually takes 15-30 minutes)"

        engine.update_stats("Starting viewport render", message)
        engine.viewport_starting_message_shown = True
        engine.tag_update()
        engine.tag_redraw()
        return

    if not engine.framebuffer or engine.framebuffer.needs_replacement(context, scene):
        engine.framebuffer = FrameBuffer(engine, context, scene)

    framebuffer = engine.framebuffer

    # Check for changes because some actions in Blender (e.g. moving the viewport
    # camera) do not trigger a view_update() call, but only a view_draw() call.
    changes = engine.exporter.get_viewport_changes(depsgraph, context)

    if changes & export.Change.REQUIRES_VIEW_UPDATE:
        engine.tag_redraw()
        # view_update(engine, context, depsgraph, changes)  # Disabled, see comment on force_session_restart()
        force_session_restart(engine)
        return
    elif changes & (export.Change.CAMERA | export.Change.MATERIAL):
        # Only update in view_draw if it is a camera update,
        # for everything else we call view_update().
        # We have to re-assign the session because it might have been
        # replaced due to filmsize change.
        engine.session = engine.exporter.update(depsgraph, context, engine.session, changes)
        engine.viewport_start_time = time()

    if utils.in_material_shading_mode(context):
        if not engine.session.IsInPause():
            engine.session.WaitNewFrame()
            engine.session.UpdateStats()
            framebuffer.update(engine.session, scene)
            engine.update_stats("", "")

            stats = engine.session.GetStats()
            samples = stats.Get("stats.renderengine.pass").GetInt()

            if samples >= 5:
                print("[Engine/Viewport] Pausing session")
                engine.session.Pause()
            else:
                engine.tag_redraw()
        framebuffer.draw(engine, context, scene)
        return

    # Check if we need to pause the viewport render
    # (note: the LuxCore stat "stats.renderengine.time" is not reliable here)
    rendered_time = time() - engine.viewport_start_time
    halt_time = scene.luxcore.viewport.halt_time
    status_message = ""

    if rendered_time > halt_time:
        if not engine.session.IsInPause():
            print("[Engine/Viewport] Pausing session")
            engine.session.Pause()
        status_message = "(Paused)"

        if framebuffer.denoiser_result_cached:
            status_message = "(Paused, Denoiser Done)"
        else:
            if framebuffer.is_denoiser_active():
                if framebuffer.is_denoiser_done():
                    status_message = "(Paused, Denoiser Done)"
                    framebuffer.load_denoiser_result(scene)
                else:
                    status_message = "(Paused, Denoiser Working ...)"
                    engine.tag_redraw()
            elif context.scene.luxcore.viewport.get_denoiser(context) == "OIDN":
                try:
                    framebuffer.start_denoiser(engine.session)
                    engine.tag_redraw()
                except Exception as error:
                    status_message = "Could not start denoiser: %s" % error
    else:
        # Not in pause yet, keep drawing
        engine.session.WaitNewFrame()
        try:
            engine.session.UpdateStats()
        except RuntimeError as error:
            print("[Engine/Viewport] Error during UpdateStats():", error)
        framebuffer.update(engine.session, scene)
        framebuffer.reset_denoiser()
        engine.tag_redraw()

    framebuffer.draw(engine, context, scene)

    # Show formatted statistics in Blender UI
    config = engine.session.GetRenderConfig()
    stats = engine.session.GetStats()
    pretty_stats = utils_render.get_pretty_stats(config, stats, scene, context)
    engine.update_stats(pretty_stats, status_message)
