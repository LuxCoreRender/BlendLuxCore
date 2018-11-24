from .. import utils

# noise threshold has to be a little greater than 0
SMALLEST_NOISE_THRESH = 0.0001


def convert(scene):
    prefix = ""
    definitions = {}

    halt = utils.get_halt_conditions(scene)

    # Set this property even if halt conditions are disabled
    # so we can use a very low haltthreshold for final renders
    # and still have endless rendering
    use_noise_thresh = halt.enable and halt.use_noise_thresh
    definitions["batch.haltthreshold.stoprendering.enable"] = use_noise_thresh

    if not use_noise_thresh:
        # Set a very low noise threshold so final renders use
        # the adaptive sampling to full advantage
        definitions["batch.haltthreshold"] = SMALLEST_NOISE_THRESH

    if halt.enable:
        halt_time = halt.time if halt.use_time else 0
        halt_spp = halt.samples if halt.use_samples else 0

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
        halt_time = 0
        halt_spp = 0

    if utils.use_two_tiled_passes(scene):
        aa = scene.luxcore.config.tile.path_sampling_aa_size
        halt_spp = max(halt_spp, 2 * aa**2)

    definitions["batch.haltspp"] = halt_spp
    definitions["batch.halttime"] = halt_time

    return utils.create_props(prefix, definitions)
