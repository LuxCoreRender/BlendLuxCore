from ..bin import pyluxcore
from .. import utils


def convert(scene, context=None):
    props = pyluxcore.Properties()
    width, height = utils.calc_filmsize(scene, context)

    props.Set(pyluxcore.Property("renderengine.type", "RTPATHCPU"))
    props.Set(pyluxcore.Property("sampler.type", "RTPATHCPUSAMPLER"))
    props.Set(pyluxcore.Property("film.width", width))
    props.Set(pyluxcore.Property("film.height", height))

    return props