from ..bin import pyluxcore
from .. import utils


def convert(scene, context=None):
    try:
        prefix = ""
        # We collect the properties in this dictionary
        # Common props are set at the end of the function
        # Very specific props that are not needed every time are set in the if/else
        # The dictionary is converted to pyluxcore.Properties() in the return statement
        definitions = {}

        # See properties/config.py
        config = scene.luxcore.config
        width, height = utils.calc_filmsize(scene, context)

        if context:
            # TODO: Support OpenCL in viewport?
            # Viewport render
            engine = "RTPATHCPU"
            sampler = "RTPATHCPUSAMPLER"
            # Size of the blocks
            definitions["rtpathcpu.zoomphase.size"] = 4
            # How to blend new samples over old ones
            # Set to 0 because otherwise bright pixels (e.g. meshlights) stay blocky for a long time
            definitions["rtpathcpu.zoomphase.weight"] = 0
        else:
            # Final render
            if config.engine == "PATH":
                if config.use_tiles:
                    engine = "TILEPATH"
                    # TILEPATH needs exactly this sampler
                    sampler = "TILEPATHSAMPLER"
                else:
                    engine = "PATH"
                    sampler = config.sampler

                # Add CPU/OCL suffix
                engine += config.device
            else:
                # config.engine == BIDIR
                engine = "BIDIRCPU"
                # SOBOL or RANDOM would be possible, but make little sense for BIDIR
                sampler = "METROPOLIS"

        # Common properties that should be set regardless of engine configuration
        # We create them as variable and set them here because then the IDE can warn us
        # if we forget some in the if/else construct above
        definitions.update({
            "renderengine.type": engine,
            "sampler.type": sampler,
            "film.width": width,
            "film.height": height,
        })

        return utils.create_props(prefix, definitions)
    except Exception as error:
        # TODO: collect exporter errors
        print("ERROR in config export")
        print(error)
        return pyluxcore.Properties()