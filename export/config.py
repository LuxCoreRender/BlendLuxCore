from ..bin import pyluxcore
from .. import utils


def convert(scene, context=None):
    config = scene.luxcore
    width, height = utils.calc_filmsize(scene, context)

    if context:
        # Viewport render
        engine = "RTPATHCPU"
        sampler = "RTPATHCPUSAMPLER"
    else:
        # Final render
        engine = config.engine
        sampler = "SOBOL"

    prefix = ""
    definitions = {
        "renderengine.type": engine,
        "sampler.type": sampler,
        "film.width": width,
        "film.height": height,
    }

    return utils.create_props(prefix, definitions)