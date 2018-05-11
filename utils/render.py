from . import calc_filmsize
from .. import utils

engine_to_str = {
    "PATHCPU": "Path CPU",
    "PATHOCL": "Path OpenCL",
    "TILEPATHCPU": "Tile Path CPU",
    "TILEPATHOCL": "Tile Path OpenCL",
    "BIDIRCPU": "Bidir CPU",
    "BIDIRVMCPU": "BidirVM CPU",
    "RTPATHOCL": "RT Path OpenCL",
    "RTPATHCPU": "RT Path CPU",
}

sampler_to_str = {
    "RANDOM": "Random",
    "SOBOL": "Sobol",
    "METROPOLIS": "Metropolis",
    "RTPATHCPUSAMPLER": "RT Path Sampler",
    "TILEPATHSAMPLER": "Tile Path Sampler"
}


def refresh(engine, scene, config, draw_film, time_until_film_refresh=0, render_stopped=False):
    """ Stats and optional film refresh during final render """
    error_message = ""
    try:
        engine.session.UpdateStats()
    except RuntimeError as error:
        print("Error during UpdateStats():", error)
        error_message = str(error)

    stats = engine.session.GetStats()

    # Show stats string in UI
    pretty_stats = get_pretty_stats(config, stats, scene)

    if draw_film:
        if engine.has_denoiser() and scene.luxcore.denoiser.refresh:
            refresh_message = "Running denoiser and refreshing film..."
        else:
            refresh_message = "Refreshing film..."
    else:
        refresh_message = "Film refresh in %ds" % time_until_film_refresh

    if error_message:
        refresh_message += " | " + error_message

    engine.update_stats(pretty_stats, refresh_message)

    if draw_film:
        # Show updated film (this operation is expensive)
        engine.framebuffer.draw(engine, engine.session, scene, render_stopped)

    # Update progress bar if we have halt conditions
    halt = utils.get_halt_conditions(scene)
    if halt.enable and (halt.use_time or halt.use_samples or halt.use_noise_thresh):
        rendered_samples = stats.Get("stats.renderengine.pass").GetInt()
        rendered_time = stats.Get("stats.renderengine.time").GetFloat()
        percent = 0

        if halt.use_time:
            percent = rendered_time / halt.time

        if halt.use_samples:
            percent_samples = rendered_samples / halt.samples
            percent = max(percent, percent_samples)

        if halt.use_noise_thresh:
            convergence = stats.Get("stats.renderengine.convergence").GetFloat()
            percent = max(percent, convergence)

        engine.update_progress(percent)
    else:
        # Reset to 0 in case the user disables the halt conditions during render
        engine.update_progress(0)


def get_pretty_stats(config, stats, scene, context=None):
    halt = utils.get_halt_conditions(scene)
    errorlog = scene.luxcore.errorlog

    # Here we collect strings in a list and later join them
    # so the result will look like: "message 1 | message 2 | ..."
    pretty = []

    # Name of the current render layer
    if len(scene.render.layers) > 1:
        render_layer = utils.get_current_render_layer(scene)
        # render_layer is None in viewport render
        if render_layer:
            pretty.append(render_layer.name)

    if context:
        # In viewport, the usual halt conditions are irrelevant, only the time counts
        rendered_time = stats.Get("stats.renderengine.time").GetFloat()
        viewport_halt_time = scene.luxcore.display.viewport_halt_time
        if rendered_time > viewport_halt_time:
            # This is only a UI issue, the render always pauses
            rendered_time = viewport_halt_time
        pretty.append("Time: %ds/%ds" % (rendered_time, viewport_halt_time))
    else:
        # Time
        if halt.enable and halt.use_time:
            rendered_time = stats.Get("stats.renderengine.time").GetFloat()
            pretty.append("Time: %ds/%ds" % (rendered_time, halt.time))

        # Samples (aka passes)
        samples = stats.Get("stats.renderengine.pass").GetInt()

        if halt.enable and halt.use_samples:
            pretty.append("%d/%d Samples" % (samples, halt.samples))
        else:
            pretty.append("%d Samples" % samples)

        # Samples/Sec
        samples_per_sec = stats.Get("stats.renderengine.total.samplesec").GetFloat()

        if samples_per_sec > 10 ** 6 - 1:
            # Use megasamples as unit
            pretty.append("Samples/Sec %.1f M" % (samples_per_sec / 10 ** 6))
        else:
            # Use kilosamples as unit
            pretty.append("Samples/Sec %d k" % (samples_per_sec / 10 ** 3))

        # Convergence (how many pixels are converged, in percent)
        convergence = stats.Get("stats.renderengine.convergence").GetFloat()
        if convergence > 0:
            if convergence < 0.95:
                convergence_msg = "%d%% Pixels Converged" % round(convergence * 100)
            else:
                convergence_msg = "%.2f Pixels Converged" % (convergence * 100)
            pretty.append(convergence_msg)

    # Engine + Sampler
    engine = config.GetProperties().Get("renderengine.type").GetString()
    sampler = config.GetProperties().Get("sampler.type").GetString()
    if engine in engine_to_str and sampler in sampler_to_str:
        pretty.append(engine_to_str[engine] + " + " + sampler_to_str[sampler])

    # Triangle count
    triangle_count = stats.Get("stats.dataset.trianglecount").GetUnsignedLongLong()
    pretty.append("{:,} Tris".format(triangle_count))

    # Errors and warnings
    error_str = ""

    if errorlog.errors:
        error_str += utils.pluralize("%d Error", len(errorlog.errors))

    if errorlog.warnings:
        if error_str:
            error_str += ", "
        error_str += utils.pluralize("%d Warning", len(errorlog.warnings))

    if error_str:
        pretty.append(error_str)

    return " | ".join(pretty)


def shortest_display_interval(scene):
    # Magic formula to compute shortest possible display interval (found through testing).
    # If the interval is any shorter, the CPU won't be able to keep up.
    # Only used for final renders.
    width, height = calc_filmsize(scene)
    return (width * height) / 852272.0 * 1.1


def find_suggested_clamp_value(session, scene=None):
    """
    Find suggested clamp value.
    If a scene is passed, the value is set in the config properties so
    the user later sees it in the render panel.
    Only do this if clamping is disabled, otherwise the value is meaningless.
    """
    avg_film_luminance = session.GetFilm().GetFilmY()
    if avg_film_luminance < 0:
        suggested_clamping_value = 0
    else:
        v = avg_film_luminance * 10
        suggested_clamping_value = v * v

    if scene:
        scene.luxcore.config.path.suggested_clamping_value = suggested_clamping_value

    return suggested_clamping_value


def find_suggested_tonemap_scale(session):
    """
    This is the same code as in the TONEMAP_AUTOLINEAR imagepipeline plugin.
    If you use the return value as the scale of the TONEMAP_LINEAR plugin,
    you emulate the autolinear tonemapper.
    """
    avg_film_luminance = session.GetFilm().GetFilmY()
    return (1.25 / avg_film_luminance * (118 / 255))

    # TODO
    # measure this all the time, show a message to the user if
    # abs(old - new) > threshold
    # so the user can set the new value with one click

    # imagepipeline = scene.camera.data.luxcore.imagepipeline
    # imagepipeline.tonemapper.linear_scale = suggested_linear_scale
    # imagepipeline.tonemapper.use_autolinear = False
