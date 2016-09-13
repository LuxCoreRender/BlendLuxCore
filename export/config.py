from ..bin import pyluxcore
from .. import utils


def convert(scene, context=None):
    print("converting config")
    props = pyluxcore.Properties()
    width, height = utils.calc_filmsize(scene, context)

    props.Set(pyluxcore.Property("renderengine.type", "PATHCPU"))
    props.Set(pyluxcore.Property("sampler.type", "SOBOL"))
    props.Set(pyluxcore.Property("film.width", width))
    props.Set(pyluxcore.Property("film.height", height))

    return props