from . import calc_filmsize

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


def refresh(engine, scene, config, draw_film, time_until_film_refresh=0):
    """ Stats and optional film refresh during final render """
    engine._session.UpdateStats()
    stats = engine._session.GetStats()

    # Show stats string in UI
    pretty_stats = get_pretty_stats(config, stats, scene.luxcore.halt)
    if draw_film:
        refresh_message = "Refreshing film..."
    else:
        refresh_message = "Film refresh in %ds" % time_until_film_refresh
    engine.update_stats(pretty_stats, refresh_message)

    if draw_film and not engine.test_break():
        # Show updated film
        engine._framebuffer.draw(engine, engine._session)

    # Update progress bar if we have halt conditions
    halt = scene.luxcore.halt
    if halt.enable and (halt.use_time or halt.use_samples):
        rendered_samples = stats.Get("stats.renderengine.pass").GetInt()
        rendered_time = stats.Get("stats.renderengine.time").GetFloat()
        percent = 0

        if halt.use_time:
            percent = rendered_time / halt.time

        if halt.use_samples:
            percent_samples = rendered_samples / halt.samples
            percent = max(percent, percent_samples)

        engine.update_progress(percent)
    else:
        # Reset to 0 in case the user disables the halt conditions during render
        engine.update_progress(0)

    return stats


def halt_condition_met(scene, stats):
    halt = scene.luxcore.halt

    if halt.enable:
        rendered_samples = stats.Get("stats.renderengine.pass").GetInt()
        rendered_time = stats.Get("stats.renderengine.time").GetFloat()

        if halt.use_time and (rendered_time > halt.time):
            print("Reached halt time: %d seconds" % halt.time)
            return True

        if halt.use_samples and (rendered_samples > halt.samples):
            print("Reached halt samples: %d samples" % halt.samples)
            return True

    return False


def get_pretty_stats(config, stats, halt):
    pretty = []

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

    # Engine + Sampler
    engine = config.GetProperties().Get("renderengine.type").GetString()
    sampler = config.GetProperties().Get("sampler.type").GetString()
    pretty.append(engine_to_str[engine] + " + " + sampler_to_str[sampler])

    # Triangle count
    triangle_count = stats.Get("stats.dataset.trianglecount").GetInt()
    pretty.append('{:,} Tris'.format(triangle_count))

    return " | ".join(pretty)


def shortest_display_interval(scene):
    # Magic formula to compute shortest possible display interval (found through testing).
    # If the interval is any shorter, the CPU won't be able to keep up.
    # Only used for final renders.
    width, height = calc_filmsize(scene)
    return (width * height) / 852272.0 * 1.1
