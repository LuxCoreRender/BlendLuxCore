from .. import utils

# noise threshold has to be a little greater than 0
SMALLEST_NOISE_THRESH = 0.0001


def convert(scene):
    prefix = ""
    definitions = {}

    halt = utils.get_halt_conditions(scene)
    config = scene.luxcore.config
    using_hybridbackforward = utils.using_hybridbackforward(scene)
    using_only_lighttracing = config.using_only_lighttracing()

    if halt.enable:
        halt_time = halt.time if halt.use_time else 0
        halt_spp_eye = halt.samples if halt.use_samples else 0
        halt_spp_light = halt.light_samples if (halt.use_light_samples
            and using_hybridbackforward and not using_only_lighttracing) else 0

        if halt.use_noise_thresh:
            if halt.noise_thresh == 0:
                noise_thresh = SMALLEST_NOISE_THRESH
            else:
                noise_thresh = halt.noise_thresh / 256

            definitions["batch.haltthreshold"] = noise_thresh
            definitions["batch.haltthreshold.warmup"] = halt.noise_thresh_warmup
            definitions["batch.haltthreshold.step"] = halt.noise_thresh_step
            definitions["batch.haltthreshold.filter.enable"] = True
            definitions["batch.haltthreshold.stoprendering.enable"] = True
    else:
        # All halt conditions disabled.
        # Note that we have to explicitly set halttime and haltspp to 0 because
        # these properties are not deleted during a session parsing.
        halt_time = 0
        halt_spp_eye = 0
        halt_spp_light = 0

    if utils.use_two_tiled_passes(scene):
        aa = scene.luxcore.config.tile.path_sampling_aa_size
        halt_spp_eye = max(halt_spp_eye, 2 * aa**2)

    # Swap halt condition if no eye samples are rendered at all
    if using_only_lighttracing:
        halt_spp_light = halt_spp_eye
        halt_spp_eye = 0

    definitions["batch.haltspp"] = [halt_spp_eye, halt_spp_light]
    definitions["batch.halttime"] = halt_time

    return utils.create_props(prefix, definitions)
