import threading
from time import time, sleep
from concurrent.futures import ThreadPoolExecutor
from .. import export, utils
from ..draw.final import FrameBufferFinal
from ..utils import render as utils_render
from ..utils.errorlog import LuxCoreErrorLog
from ..utils import view_layer as utils_view_layer
from ..properties.denoiser import LuxCoreDenoiser
from ..properties.display import LuxCoreDisplaySettings


def render(engine, depsgraph):
    print("=" * 50)
    scene = depsgraph.scene_eval
    LuxCoreErrorLog.clear()
    statistics = scene.luxcore.statistics.get_active()

    if utils.is_valid_camera(scene.camera):
        tonemapper = scene.camera.data.luxcore.imagepipeline.tonemapper
        if len(scene.view_layers) > 1 and tonemapper.is_automatic():
            msg = ("Using an automatic tonemapper with multiple "
                   "renderlayers will result in brightness differences")
            LuxCoreErrorLog.add_warning(msg)

    _check_halt_conditions(engine, scene)

    # Using ThreadPoolExecutor to manage threads efficiently
    with ThreadPoolExecutor(max_workers=4) as executor:  # Limit the number of concurrent threads
        futures = []
        for layer_index, layer in enumerate(scene.view_layers):
            if layer.use:
                futures.append(executor.submit(_render_layer_thread, engine, depsgraph, statistics, layer))

        for future in futures:
            future.result()  # Wait for all threads to finish


def _render_layer_thread(engine, depsgraph, statistics, layer):
    """
    A thread-specific function to render a single layer.
    """
    print(f'[Engine/Final] Rendering layer "{layer.name}"')

    dummy_result = engine.begin_result(0, 0, 1, 1, layer=layer.name)

    if layer.name not in dummy_result.layers:
        engine.end_result(dummy_result, cancel=True, do_merge_results=False)
        return

    engine.end_result(dummy_result, cancel=True, do_merge_results=False)

    # This property is used during export, e.g. to check for layer visibility
    utils_view_layer.State.active_view_layer = layer.name

    _add_passes(engine, layer, depsgraph.scene)
    _render_layer(engine, depsgraph, statistics, layer)


def _render_layer(engine, depsgraph, statistics, view_layer):
    engine.reset()
    engine.exporter = export.Exporter(statistics)
    engine.session = engine.exporter.create_session(depsgraph, engine=engine, view_layer=view_layer)
    scene = depsgraph.scene_eval

    if engine.session is None:
        # session is None, but no error was thrown
        print("[Engine/Final] Export cancelled by user.")
        return

    engine.framebuffer = FrameBufferFinal(scene)

    # Create session
    start = time()
    engine.session.Start()  # Start session only once
    session_init_time = time() - start
    print("Session started in %.1f s" % session_init_time)
    statistics.session_init_time.value = session_init_time

    config = engine.session.GetRenderConfig()

    if scene.luxcore.config.use_filesaver:
        engine.session.Stop()

        if scene.luxcore.config.filesaver_format == "BIN":
            output_path = config.GetProperties().Get("filesaver.filename").GetString()
        else:
            output_path = config.GetProperties().Get("filesaver.directory").GetString()
        engine.report({"INFO"}, 'Exported to "%s"' % output_path)

        # Clean up
        del engine.session
        engine.session = None
        return

    start = time()
    path_settings = scene.luxcore.config.path
    last_film_refresh = 0
    last_stat_refresh = 0
    checked_optimal_clamp = path_settings.use_clamping
    engine_type = config.GetProperties().Get("renderengine.type").GetString()
    if engine_type.startswith("TILE"):
        epsilon = 0.1
        aa = scene.luxcore.config.tile.path_sampling_aa_size
        clamp_warmup_samples = aa**2 - epsilon
    else:
        clamp_warmup_samples = 2.0
    stats = utils_render.update_stats(engine.session)
    FAST_REFRESH_DURATION = 1 if engine.is_animation else 5

    while True:
        now = time()
        manual_refresh_requested = LuxCoreDisplaySettings.refresh or LuxCoreDenoiser.refresh
        update_stats = (now - last_stat_refresh) > _stat_refresh_interval(start, scene)
        time_until_film_refresh = depsgraph.scene.luxcore.display.interval - (now - last_film_refresh)
        fast_refresh = now - start < FAST_REFRESH_DURATION

        if LuxCoreDisplaySettings.paused:
            if not engine.session.IsInPause():
                engine.session.Pause()
                utils_render.update_status_msg(stats, engine, depsgraph.scene, config, time_until_film_refresh=0)
                engine.framebuffer.draw(engine, engine.session, depsgraph.scene, render_stopped=False)
                engine.update_stats("", "Paused")
        else:
            if engine.session.IsInPause():
                engine.session.Resume()

        changes = engine.exporter.get_changes(depsgraph)
        engine.exporter.update_session(changes, engine.session)

        if engine.session.IsInPause():
            if changes or manual_refresh_requested:
                engine.framebuffer.draw(engine, engine.session, depsgraph.scene, render_stopped=False)
        else:
            if fast_refresh or update_stats or changes or manual_refresh_requested or (time_until_film_refresh <= 0):
                draw_film = fast_refresh or (time_until_film_refresh <= 0)
                draw_film |= changes or manual_refresh_requested

                stats = utils_render.update_stats(engine.session)
                if draw_film:
                    time_until_film_refresh = 0
                utils_render.update_status_msg(stats, engine, depsgraph.scene, config, time_until_film_refresh)

                if _stop_requested(engine) or engine.session.HasDone():
                    break

                last_stat_refresh = now
                if draw_film:
                    engine.framebuffer.draw(engine, engine.session, depsgraph.scene, render_stopped=False)
                    last_film_refresh = now

            utils_render.update_status_msg(stats, engine, depsgraph.scene, config, time_until_film_refresh)

            samples = stats.Get("stats.renderengine.pass").GetInt()
            if not checked_optimal_clamp and samples > clamp_warmup_samples:
                clamp_value = utils_render.find_suggested_clamp_value(engine.session, depsgraph.scene)
                print("Recommended clamp value:", clamp_value)
                checked_optimal_clamp = True

        if _stop_requested(engine):
            break

        sleep(1 / 5)  # Reduce refresh rate for better performance

    stats = utils_render.update_stats(engine.session)
    utils_render.update_status_msg(stats, engine, depsgraph.scene, config, time_until_film_refresh=0)
    engine.framebuffer.draw(engine, engine.session, depsgraph.scene, render_stopped=True)
    engine.update_stats("Render", "Stopping session...")
    if engine.session.IsInPause():
        engine.session.Resume()
    engine.session.Stop()
    del engine.session
    engine.session = None


def _stop_requested(engine):
    return engine.test_break() or LuxCoreDisplaySettings.stop_requested


def _stat_refresh_interval(start, scene):
    width, height = utils_render.calc_filmsize(scene)
    is_big_image = width * height > 2000 * 2000
    minimum = 4 if is_big_image else 1
    maximum = 16

    minutes = (time() - start) / 60
    if minutes < 4:
        return max(2**minutes, minimum)
    else:
        return maximum


def _check_halt_conditions(engine, scene):
    enabled_layers = [layer for layer in scene.view_layers if layer.use]
    needs_halt_condition = len(enabled_layers) > 1 or engine.is_animation

    is_halt_enabled = True

    if len(enabled_layers) > 1:
        for layer in enabled_layers:
            layer_halt = layer.luxcore.halt
            if layer_halt.enable:
                has_halt_condition = layer_halt.is_enabled()
                is_halt_enabled &= has_halt_condition

                if not has_halt_condition:
                    LuxCoreErrorLog.add_error('Halt condition missing for render layer "%s"' % layer.name)
            else:
                is_halt_enabled = False

    if not is_halt_enabled:
        is_halt_enabled = scene.luxcore.halt.is_enabled()

    if needs_halt_condition and not is_halt_enabled:
        raise Exception("Missing halt condition (check error log)")


def _add_passes(engine, layer, scene):
    aovs = layer.luxcore.aovs
    if scene.luxcore.denoiser.enabled:
        transparent = scene.camera.data.luxcore.imagepipeline.transparent_film
        if transparent:
            engine.add_pass("DENOISED", 4, "RGBA", layer=layer.name)
        else:
            engine.add_pass("DENOISED", 3, "RGB", layer=layer.name)
    if aovs.rgb:
        engine.add_pass("RGB", 3, "RGB", layer=layer.name)
    if aovs.rgba:
        engine.add_pass("RGBA", 4, "RGBA", layer=layer.name)
    if aovs.alpha:
        engine.add_pass("ALPHA", 1, "A", layer=layer.name)
    if aovs.depth and not layer.use_pass_z:
        engine.add_pass("Depth", 1, "Z", layer=layer.name)
    if aovs.albedo:
        engine.add_pass("ALBEDO", 3, "RGB", layer=layer.name)
    if aovs.material_id:
        engine.add_pass("MATERIAL_ID", 1, "X", layer=layer.name)
    if aovs.material_id_color:
        engine.add_pass("MATERIAL_ID_COLOR", 3, "RGB", layer=layer.name)
    if aovs.object_id:
        engine.add_pass("OBJECT_ID", 1, "X", layer=layer.name)
    if aovs.emission:
        engine.add_pass("EMISSION", 3, "RGB", layer=layer.name)
    if aovs.caustic:
        engine.add_pass("CAUSTIC", 3, "RGB", layer=layer.name)
    if aovs.direct_diffuse:
        engine.add_pass("DIRECT_DIFFUSE", 3, "RGB", layer=layer.name)
    if aovs.direct_glossy:
        engine.add_pass("DIRECT_GLOSSY", 3, "RGB", layer=layer.name)
    if aovs.indirect_diffuse:
        engine.add_pass("INDIRECT_DIFFUSE", 3, "RGB", layer=layer.name)
