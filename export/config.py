from ..bin import pyluxcore
from .. import utils


def convert(scene, context=None):
    try:
        config = scene.luxcore.config
        width, height = utils.calc_filmsize(scene, context)

        if context:
            # Viewport render
            engine = "RTPATHCPU"
            sampler = "RTPATHCPUSAMPLER"
        else:
            # Final render
            engine = config.engine

            if engine == "TILEPATHCPU":
                sampler = "TILEPATHSAMPLER"
            else:
                sampler = config.sampler

        prefix = ""
        definitions = {
            "renderengine.type": engine,
            "sampler.type": sampler,
            "film.width": width,
            "film.height": height,
        }

        return utils.create_props(prefix, definitions)
    except Exception as error:
        # TODO: collect exporter errors
        print("ERROR in config export")
        print(error)
        return pyluxcore.Properties()