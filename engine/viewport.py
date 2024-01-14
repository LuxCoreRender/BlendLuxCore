import numpy as np
from time import time
from ..bin import pyluxcore
from .. import export
from ..draw.viewport import FrameBuffer
from .. import utils
from ..utils import render as utils_render
from ..utils.errorlog import LuxCoreErrorLog
from ..export.config import convert_viewport_engine

def start_session(engine):
    try:
        engine.session.Start()
        engine.viewport_start_time = time()
    except (ReferenceError, Exception) as error:
        handle_exception(engine, error)
    finally:
        engine.starting_session = False

def handle_exception(engine, error):
    engine.session, engine.exporter = None, None
    engine.update_stats(f"Error: {error}")
    LuxCoreErrorLog.add_error(error)
    __import__('traceback').print_exc()

def force_session_restart(engine):
    engine.session.Stop()
    engine.session = None

def view_update(engine, context, depsgraph, changes=None):
    start = time()

    if engine.starting_session or engine.viewport_fatal_error:
        return

    LuxCoreErrorLog.clear(force_ui_update=False)

    if engine.session is None:
        if not engine.viewport_starting_message_shown:
            return

        if not engine.is_first_viewport_start:
            filmsize = np.array(utils.calc_filmsize(depsgraph.scene_eval, context))
            if np.array_equal(engine.last_viewport_size, filmsize) or (time() - engine.time_of_last_viewport_resize < engine.VIEWPORT_RESIZE_TIMEOUT):
                engine.last_viewport_size = filmsize
                engine.time_of_last_viewport_resize = time()
                return

        try:
            print("=" * 50)
            print("[Engine/Viewport] New session")
            engine.exporter = export.Exporter()
            engine.session = engine.exporter.create_session(depsgraph, context, engine=engine)
            engine.starting_session = True
            engine.is_first_viewport_start = False
            import _thread
            _thread.start_new_thread(start_session, (engine,))
        except Exception as error:
            handle_exception(engine, error)

        return

    s = time()
    changes = engine.exporter.get_changes(depsgraph, context, changes)
    print("view_update(): checking for changes took %.1f ms" % ((time() - s) * 1000))

    if changes and changes & export.Change.REQUIRES_VIEW_UPDATE:
        force_session_restart(engine)
        return

    s = time()
    engine.session = engine.exporter.update(depsgraph, context, engine.session, changes)
    engine.viewport_start_time = time()

    if engine.framebuffer:
        engine.framebuffer.reset_denoiser()
    print("view_update(): applying changes took %.1f ms" % ((time() - s) * 1000))

    print("view_update() took %.1f ms" % ((time() - start) * 1000))

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
        engine.tag_redraw()
        force_session_restart(engine)
        return
    elif changes & export.Change.CAMERA:
        engine.session = engine.exporter.update(depsgraph, context, engine.session, export.Change.CAMERA)
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
        engine.session.WaitNewFrame()
        try:
            engine.session.UpdateStats()
        except RuntimeError as error:
            print("[Engine/Viewport] Error during UpdateStats():", error)
        framebuffer.update(engine.session, scene)
        framebuffer.reset_denoiser()
        engine.tag_redraw()

    framebuffer.draw(engine, context, scene)

    config = engine.session.GetRenderConfig()
    stats = engine.session.GetStats()
    pretty_stats = utils_render.get_pretty_stats(config, stats, scene, context)
    engine.update_stats(pretty_stats, status_message)
