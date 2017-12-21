
def halt_condition_met(scene, stats):
    halt = scene.luxcore.halt

    rendered_samples = stats.Get('stats.renderengine.pass').GetInt()
    rendered_time = stats.Get('stats.renderengine.time').GetFloat()

    if halt.use_time and (rendered_time > halt.time):
        print("Reached halt time: %d seconds" % halt.time)
        return True

    if halt.use_samples and (rendered_samples > halt.samples):
        print("Reached halt samples: %d samples" % halt.samples)
        return True

    return False
