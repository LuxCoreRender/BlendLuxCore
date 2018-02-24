from time import time, sleep
from .. import export
from ..draw import FrameBufferFinal
from ..utils import render as utils_render


def update(engine, scene):
    assert engine.session is None
    engine.update_stats("Export", "exporting...")

    # Create a new exporter instance.
    # This is only needed when scene.render.use_persistent_data is enabled
    # because in that case our instance of LuxCoreRenderEngine is re-used
    # See https://github.com/LuxCoreRender/BlendLuxCore/issues/59
    engine.exporter = export.Exporter()

    engine.session = engine.exporter.create_session(scene, engine=engine)
    

def render(engine, scene):
    if engine.session is None:
        # session is None, but engine.error is not set -> User cancelled.
        print("Export cancelled by user.")
        return

    engine.update_stats("Render", "Starting session...")
    engine.framebuffer = FrameBufferFinal(scene)
    engine.add_passes(scene)
    engine.session.Start()

    config = engine.session.GetRenderConfig()
    done = False
    start = time()

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

    # Fast refresh on startup so the user quickly sees an image forming.
    # Not used during animation render to enhance performance.
    if not engine.is_animation:
        FAST_REFRESH_DURATION = 5
        refresh_interval = utils_render.shortest_display_interval(scene)
        last_refresh = 0

        while not done:
            now = time()

            if now - last_refresh > refresh_interval:
                utils_render.refresh(engine, scene, config, draw_film=True)
                done = engine.test_break() or engine.session.HasDone()

            if now - start > FAST_REFRESH_DURATION:
                # It's time to switch to the loop with slow refresh below
                break

            # This is a measure to make cancelling more responsive in this phase
            checks = 10
            for i in range(checks):
                if engine.test_break():
                    done = True
                    break
                sleep(1 / 60 / checks)

    # Main loop where we refresh according to user-specified interval
    last_film_refresh = time()
    stat_refresh_interval = 1
    last_stat_refresh = time()
    computed_optimal_clamp = False

    while not engine.test_break() and not done:
        now = time()

        if now - last_stat_refresh > stat_refresh_interval:
            # We have to check the stats often to see if a halt condition is met
            # But film drawing is expensive, so we don't do it every time we check stats
            time_until_film_refresh = scene.luxcore.display.interval - (now - last_film_refresh)
            draw_film = time_until_film_refresh <= 0

            # Do session update (imagepipeline, lightgroups)
            changes = engine.exporter.get_changes(scene)
            engine.exporter.update_session(changes, engine.session)
            # Refresh quickly when user changed something
            draw_film |= changes

            utils_render.refresh(engine, scene, config, draw_film, time_until_film_refresh)
            done = engine.test_break() or engine.session.HasDone()

            last_stat_refresh = now
            if draw_film:
                last_film_refresh = now

        # Compute and print the optimal clamp value. Done only once after a warmup phase.
        # Only do this if clamping is disabled, otherwise the value is meaningless.
        path_settings = scene.luxcore.config.path
        if not computed_optimal_clamp and not path_settings.use_clamping and time() - start > 10:
            optimal_clamp = utils_render.find_suggested_clamp_value(engine.session, scene)
            print("Recommended clamp value:", optimal_clamp)
            computed_optimal_clamp = True

        # Don't use up too much CPU time for this refresh loop, but stay responsive
        sleep(1 / 60)

    # User wants to stop or halt condition is reached
    # Update stats to refresh film and draw the final result
    utils_render.refresh(engine, scene, config, draw_film=True)
    engine.update_stats("Render", "Stopping session...")
    engine.session.Stop()
    # Clean up
    del engine.session
    engine.session = None