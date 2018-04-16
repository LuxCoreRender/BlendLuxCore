from .. import utils


def convert(scene):
    prefix = ""
    definitions = {}

    halt = utils.get_halt_conditions(scene)

    # Set this property even if halt conditions are disabled
    # so we can use a very low haltthreshold for final renders
    # and still have endless rendering
    use_noise_thresh = halt.enable and halt.use_noise_thresh
    definitions["batch.haltthreshold.stoprendering.enable"] = use_noise_thresh

    # noise threshold has to be a little greater than 0
    SMALLEST_NOISE_THRESH = 0.0001

    if not use_noise_thresh:
        # Set a very low noise threshold so final renders use
        # the adaptive sampling to full advantage
        definitions["batch.haltthreshold"] = SMALLEST_NOISE_THRESH

    if halt.enable:
        if halt.use_time:
            definitions["batch.halttime"] = halt.time
        else:
            definitions["batch.halttime"] = 0

        if halt.use_samples:
            definitions["batch.haltspp"] = halt.samples
        else:
            definitions["batch.haltspp"] = 0

        if halt.use_noise_thresh:
            if halt.noise_thresh == 0:
                noise_thresh = SMALLEST_NOISE_THRESH
            else:
                noise_thresh = halt.noise_thresh / 256

            definitions["batch.haltthreshold"] = noise_thresh
            definitions["batch.haltthreshold.warmup"] = halt.noise_thresh_warmup
            definitions["batch.haltthreshold.step"] = halt.noise_thresh_step
            definitions["batch.haltthreshold.filter.enable"] = halt.noise_thresh_use_filter
    else:
        # All halt conditions disabled.
        # Note that we have to explicitly set halttime and haltspp to 0 because
        # these properties are not deleted during a session parsing.
        definitions["batch.halttime"] = 0
        definitions["batch.haltspp"] = 0

    return utils.create_props(prefix, definitions)
