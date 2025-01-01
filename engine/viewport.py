from time import time
import pyluxcore
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
    except ReferenceError:
        return
    except Exception as error:
        engine.session = None
        engine.exporter = None

        engine.update_stats("Error: ", str(error))
        LuxCoreErrorLog.add_error(error)

        import traceback
        traceback.print_exc()

    engine.starting_session = False

def force_session_restart(engine):
    if engine.session is not None:
        engine.session.Stop()
        engine.session = None

def apply_color_management_changes(engine, scene, context):
    view_settings = scene.view_settings
    exposure = view_settings.exposure
    gamma = view_settings.gamma

    if engine.session is not None:
        config = engine.session.GetRenderConfig()

        props = pyluxcore.Properties()
        props.Set(pyluxcore.Property("film.imagepipeline.0.gamma", gamma))
        props.Set(pyluxcore.Property("film.imagepipeline.0.exposure", exposure))

        # Apply the new properties
        config.Parse(props)

        # Notify LuxCore to update the frame buffer without restarting
        if hasattr(engine.session, 'UpdateFilmSettings'):
            engine.session.UpdateFilmSettings(props)

def check_color_management_changes(engine, scene):
    view_settings = scene.view_settings

    # Initialize these attributes if they don't exist yet
    if not hasattr(engine, 'last_exposure'):
        engine.last_exposure = view_settings.exposure
    if not hasattr(engine, 'last_gamma'):
        engine.last_gamma = view_settings.gamma
    if not hasattr(engine, 'last_view_transform'):
        engine.last_view_transform = getattr(view_settings, 'view_transform', None)

    # Check if the exposure, gamma, or view transform have changed
    exposure_changed = view_settings.exposure != engine.last_exposure
    gamma_changed = view_settings.gamma != engine.last_gamma
    view_transform_changed = view_settings.view_transform != engine.last_view_transform

    # Update the stored values for the next comparison
    engine.last_exposure = view_settings.exposure
    engine.last_gamma = view_settings.gamma
    engine.last_view_transform = view_settings.view_transform

    # If any of the values changed, return True
    if exposure_changed or gamma_changed or view_transform_changed:
        # Handle view transform changes separately
        if view_transform_changed:
            if view_settings.view_transform in ['AgX', 'Filmic', 'Khronos PBR Neutral']:
                # Return False if only the view transform changed, True otherwise
                return not (exposure_changed or gamma_changed)
        return True

    return False

def view_update(engine, context, depsgraph, changes=None):
    start = time()

    if engine.starting_session or engine.viewport_fatal_error:
        return

    LuxCoreErrorLog.clear(force_ui_update=False)

    if engine.session is None:
        if not engine.viewport_starting_message_shown:
            return

        if not engine.is_first_viewport_start:
            filmsize = utils.calc_filmsize(depsgraph.scene, context)
            was_resized = engine.last_viewport_size != filmsize
            engine.last_viewport_size = filmsize

            if was_resized:
                engine.time_of_last_viewport_resize = time()
                return
            elif time() - engine.time_of_last_viewport_resize < engine.VIEWPORT_RESIZE_TIMEOUT:
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
            engine.session = None
            engine.exporter = None
            engine.viewport_fatal_error = str(error)

            engine.update_stats("Error: ", str(error))
            LuxCoreErrorLog.add_error(error)

            import traceback
            traceback.print_exc()
        return

    # Check for color management changes
    if check_color_management_changes(engine, depsgraph.scene):
        apply_color_management_changes(engine, depsgraph.scene, context)
        engine.tag_redraw()
        return

    # Regular session update logic
    changes = engine.exporter.get_changes(depsgraph, context, changes)

    if changes:
        if changes & export.Change.REQUIRES_VIEW_UPDATE:
            # Only restart the session if the view transform didn't change by itself
            force_session_restart(engine)
            return

        # Update session with changes
        engine.session = engine.exporter.update(depsgraph, context, engine.session, changes)
        engine.viewport_start_time = time()

        if engine.framebuffer:
            engine.framebuffer.reset_denoiser()

    print("view_update() took %.1f ms" % ((time() - start) * 1000))


def view_draw(engine, context, depsgraph):
    scene = depsgraph.scene

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
    elif changes & (export.Change.CAMERA | export.Change.MATERIAL):
        # Update session with changes
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
        engine.session.UpdateStats()
        framebuffer.update(engine.session, scene)
        framebuffer.reset_denoiser()
        engine.tag_redraw()

    framebuffer.draw(engine, context, scene)

    # Show formatted statistics in Blender UI
    config = engine.session.GetRenderConfig()
    stats = engine.session.GetStats()
    pretty_stats = utils_render.get_pretty_stats(config, stats, scene, context)
    engine.update_stats(pretty_stats, status_message)
