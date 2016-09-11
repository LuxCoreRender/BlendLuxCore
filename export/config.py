from ..bin import pyluxcore
from .. import utils


def convert(scene):
    print("converting config")
    props = pyluxcore.Properties()
    width, height = utils.calc_filmsize(scene)

    props.Set(pyluxcore.Property("renderengine.type", "PATHCPU"))
    props.Set(pyluxcore.Property("film.width", width))
    props.Set(pyluxcore.Property("film.height", height))

    return props