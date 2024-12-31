from time import time
import pyluxcore
from .. import export
from ..draw.viewport import FrameBuffer
from .. import utils
from ..utils import render as utils_render
from ..utils.errorlog import LuxCoreErrorLog
from ..export.config import convert_viewport_engine
import threading
import traceback

# Executed in separate thread
def start_session(engine):
    try:
        engine.session.Start()
        engine.viewport_start_time = time()
    except ReferenceError:
        # Could not start render session because RenderEngine struct was deleted (caused
        # by the user cancelling the viewport render before this function is called)
        return
    except (pyluxcore.LuxCoreError, RuntimeError) as error:
        # Catch LuxCore specific errors or runtime errors
        engine.session = None
        engine.exporter = None
        engine.viewport_fatal_error = f"LuxCoreError: {str(error)}"
        LuxCoreErrorLog.add_error(error)
        engine.update_stats("Error: ", str(error))
        traceback.print_exc()
    except Exception as error:
        # Generic exception handler
        engine.session = None
        engine.exporter = None
        engine.viewport_fatal_error = f"General Error: {str(error)}"
        LuxCoreErrorLog.add_error(error)
        engine.update_stats("Error: ", str(error))
        traceback.print_exc()

    # Note: Due to CPython implementation details, it's not necessary to use a lock here (this modification is atomic)
    engine.starting_session = False


def force_session_restart(engine):
    """
    For unknown reasons, the old way of handling changes to the renderconfig causes a memory leak.
    As a workaround, this method stops and deletes the session to trigger a full re-export of the scene.
    """
    if engine.session:
        try:
            engine.session.Stop()
        except Exception as error:
            LuxCoreErrorLog.add_error(f"Error stopping session: {error}")
            traceback.print_exc()
    engine.session = None
    engine.exporter = None


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
                # Don't re-export the session before the timeout is done
                return
        
        try:
            print("=" * 50)
            print("[Engine/Viewport] New session")
            engine.exporter = export.Exporter()
            engine.session = engine.exporter.create_session(depsgraph, context, engine=engine)
            # Start in separate thread to avoid blocking the UI
            engine.starting_session = True
            engine.is_first_viewport_start = False
            threading.Thread(target=start_session, args=(engine,), daemon=True).start()
        except (pyluxcore.LuxCoreError, RuntimeError) as error:
            engine.session = None
            engine.exporter = None
            engine.viewport_fatal_error = f"LuxCoreError: {str(error)}"
            LuxCoreErrorLog.add_error(error)
            traceback.print_exc()
        except Exception as error:
            engine.session = None
            engine.exporter = None
            engine.viewport_fatal_error = f"General Error: {str(error)}"
            LuxCoreErrorLog.add_error(error)
            traceback.print_exc()

        return

    # Handle changes to the scene, like geometry, camera, etc.
    s = time()
    changes = engine.exporter.get_changes(depsgraph, context, changes)
    print(f"view_update(): checking for changes took {(time() - s) * 1000:.1f} ms")

    if changes:
        if changes & export.Change.REQUIRES_VIEW_UPDATE:
            force_session_restart(engine)
            return

        s = time()
        engine.session = engine.exporter.update(depsgraph, context, engine.session, changes)
        engine.viewport_start_time = time()

        if engine.framebuffer:
            engine.framebuffer.reset_denoiser()
        print(f"view_update(): applying changes took {(time() - s) * 1000:.1f} ms")
    
    print(f"view_update() took {(time() - start) * 1000:.1f} ms")


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

    changes = engine.exporter.get_viewport_changes(depsgraph, context)

    if changes & export.Change.REQUIRES_VIEW_UPDATE:
        force_session_restart(engine)
        return
    elif changes & export.Change.CAMERA:
        engine.session = engine.exporter.update(depsgraph, context, engine.session, export.Change.CAMERA)
        engine.viewport_start_time = time()

    # Denoising and performance logic
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
                    status_message = f"Could not start denoiser: {error}"
    else:
        engine.session.WaitNewFrame()
        try:
            engine.session.UpdateStats()
        except RuntimeError as error:
            print(f"[Engine/Viewport] Error during UpdateStats(): {error}")
        framebuffer.update(engine.session, scene)
        framebuffer.reset_denoiser()
        engine.tag_redraw()

    framebuffer.draw(engine, context, scene)

    # Show formatted statistics in Blender UI
    config = engine.session.GetRenderConfig()
    stats = engine.session.GetStats()
    pretty_stats = utils_render.get_pretty_stats(config, stats, scene, context)
    engine.update_stats(pretty_stats, status_message)
