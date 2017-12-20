from ..bin import pyluxcore
from .. import utils


def convert(scene, context=None):
    try:
        prefix = ""
        # We collect the properties in this dictionary.
        # Common props are set at the end of the function.
        # Very specific props that are not needed every time are set in the if/else.
        # The dictionary is converted to pyluxcore.Properties() in the return statement.
        definitions = {}

        # See properties/config.py
        config = scene.luxcore.config
        width, height = utils.calc_filmsize(scene, context)

        if context:
            # TODO: Support OpenCL in viewport?
            # Viewport render
            engine = "RTPATHCPU"
            sampler = "RTPATHCPUSAMPLER"
            # Size of the blocks right after a scene edit (in pixels)
            definitions["rtpathcpu.zoomphase.size"] = 4
            # How to blend new samples over old ones.
            # Set to 0 because otherwise bright pixels (e.g. meshlights) stay blocky for a long time.
            definitions["rtpathcpu.zoomphase.weight"] = 0
            _convert_path(config, definitions)
        else:
            # Final render
            if config.engine == "PATH":
                # Specific settings for PATH and TILEPATH
                _convert_path(config, definitions)

                if config.use_tiles:
                    engine = "TILEPATH"
                    # TILEPATH needs exactly this sampler
                    sampler = "TILEPATHSAMPLER"
                    # Tile specific settings
                    tile = config.tile
                    definitions["tilepath.sampling.aa.size"] = tile.path_sampling_aa_size
                    definitions["tile.size"] = tile.size
                    definitions["tile.multipass.enable"] = tile.multipass_enable
                    thresh = tile.multipass_convtest_threshold
                    definitions["tile.multipass.convergencetest.threshold"] = thresh
                    thresh_reduct = tile.multipass_convtest_threshold_reduction
                    definitions["tile.multipass.convergencetest.threshold.reduction"] = thresh_reduct
                    # TODO do we need to expose this? In LuxBlend we didn't
                    # warmup = tile.multipass_convtest_warmup
                    # definitions["tile.multipass.convergencetest.warmup.count"] = warmup
                else:
                    engine = "PATH"
                    sampler = config.sampler

                # Add CPU/OCL suffix
                engine += config.device

                if config.device == "OCL":
                    # OpenCL specific settings
                    definitions["opencl.cpu.use"] = config.opencl.use_cpu
                    definitions["opencl.gpu.use"] = config.opencl.use_gpu
                    # TODO opencl.devices.select
            else:
                # config.engine == BIDIR
                engine = "BIDIRCPU"
                # SOBOL or RANDOM would be possible, but make little sense for BIDIR
                sampler = "METROPOLIS"
                definitions["light.maxdepth"] = config.bidir_light_maxdepth
                definitions["path.maxdepth"] = config.bidir_path_maxdepth

        # Common properties that should be set regardless of engine configuration.
        # We create them as variables and set them here because then the IDE can warn us
        # if we forget some in the if/else construct above.
        definitions.update({
            "renderengine.type": engine,
            "sampler.type": sampler,
            "film.width": width,
            "film.height": height,
        })

        # TODO: remove this once we properly implement the imagepipeline
        # very crude imagepipeline, just for now so final matches viewport
        definitions["film.outputs.1.type"] = "RGB_IMAGEPIPELINE"
        definitions["film.outputs.1.filename"] = "RGB_IMAGEPIPELINE.png"
        definitions["film.imagepipeline.0.type"] = "TONEMAP_AUTOLINEAR"
        if context:
            # Viewport render needs gamma correction
            definitions["film.imagepipeline.1.type"] = "GAMMA_CORRECTION"
            definitions["film.imagepipeline.1.value"] = 2.2
        else:
            # Final render needs to be made darker so it matches viewport
            # TODO this is hopefully no longer necessary once we can use
            # the Blender colorspace fragment shader in viewport drawing
            definitions["film.imagepipeline.1.type"] = "TONEMAP_LINEAR"
            definitions["film.imagepipeline.1.scale"] = 1 / 2.25


        return utils.create_props(prefix, definitions)
    except Exception as error:
        # TODO: collect exporter errors
        print("ERROR in config export")
        print(error)
        return pyluxcore.Properties()


def _convert_path(config, definitions):
    path = config.path
    definitions["path.pathdepth.total"] = path.depth_total
    definitions["path.pathdepth.diffuse"] = path.depth_diffuse
    definitions["path.pathdepth.glossy"] = path.depth_glossy
    definitions["path.pathdepth.specular"] = path.depth_specular
    # TODO path.forceblackbackground.enable (if film is transparent)

    if path.use_clamping:
        definitions["path.clamping.variance.maxvalue"] = path.clamping
