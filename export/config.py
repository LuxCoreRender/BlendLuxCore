import os
import errno
import bpy
from ..bin import pyluxcore
from .. import utils
from . import aovs
from .imagepipeline import use_backgroundimage


def convert(scene, context=None, engine=None):
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
            luxcore_engine = "RTPATHCPU"
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
                    luxcore_engine = "TILEPATH"
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
                    luxcore_engine = "PATH"
                    sampler = config.sampler
                    definitions["sampler.sobol.adaptive.strength"] = config.sobol_adaptive_strength
                    _convert_metropolis_settings(definitions, config)

                # Add CPU/OCL suffix
                luxcore_engine += config.device

                if config.device == "OCL":
                    # OpenCL specific settings
                    opencl = scene.luxcore.opencl
                    definitions["opencl.cpu.use"] = False
                    definitions["opencl.gpu.use"] = True
                    definitions["opencl.devices.select"] = opencl.devices_to_selection_string()

                    # OpenCL CPU (hybrid render) thread settings (we use the properties from Blender here)
                    if opencl.use_native_cpu:
                        if scene.render.threads_mode == "FIXED":
                            # Explicitly set the number of threads
                            definitions["opencl.native.threads.count"] = scene.render.threads
                        # If no thread count is specified, LuxCore automatically uses all available cores
                    else:
                        # Disable hybrid rendering
                        definitions["opencl.native.threads.count"] = 0
            else:
                # config.engine == BIDIR
                luxcore_engine = "BIDIRCPU"
                # SOBOL or RANDOM would be possible, but make little sense for BIDIR
                sampler = "METROPOLIS"
                _convert_metropolis_settings(definitions, config)
                definitions["light.maxdepth"] = config.bidir_light_maxdepth
                definitions["path.maxdepth"] = config.bidir_path_maxdepth

        # Common properties that should be set regardless of engine configuration.
        # We create them as variables and set them here because then the IDE can warn us
        # if we forget some in the if/else construct above.
        definitions.update({
            "renderengine.type": luxcore_engine,
            "sampler.type": sampler,
            "film.width": width,
            "film.height": height,
            "film.filter.type": config.filter,
            "film.filter.width": config.filter_width,
            "lightstrategy.type": config.light_strategy,
            "scene.epsilon.min": config.min_epsilon,
            "scene.epsilon.max": config.max_epsilon,
        })

        if config.path.use_clamping:
            definitions["path.clamping.variance.maxvalue"] = config.path.clamping

        # Filter
        if config.filter == "GAUSSIAN":
            definitions["film.filter.gaussian.alpha"] = config.gaussian_alpha

        use_filesaver = utils.use_filesaver(context, scene)

        # Transparent film settings
        black_background = False
        if scene.camera:
            pipeline = scene.camera.data.luxcore.imagepipeline

            if (pipeline.transparent_film or use_backgroundimage(context, scene)) and not use_filesaver:
                # This avoids issues with transparent film in Blender
                black_background = True
        definitions["path.forceblackbackground.enable"] = black_background

        # FILESAVER engine (only in final render)
        if use_filesaver:
            _convert_filesaver(scene, definitions, luxcore_engine)

        # CPU thread settings (we use the properties from Blender here)
        if scene.render.threads_mode == "FIXED":
            definitions["native.threads.count"] = scene.render.threads

        _convert_seed(scene, definitions)

        # Create the properties
        config_props = utils.create_props(prefix, definitions)

        # Convert AOVs
        aov_props = aovs.convert(scene, context, engine)
        config_props.Set(aov_props)

        return config_props
    except Exception as error:
        msg = 'Config: %s' % error
        # Note: Exceptions in the config are critical, we can't render without a config
        scene.luxcore.errorlog.add_error(msg)
        return pyluxcore.Properties()


def _convert_path(config, definitions):
    path = config.path
    # Note that for non-specular paths +1 is added to the path depth.
    # For details see http://www.luxrender.net/forum/viewtopic.php?f=11&t=11101&start=390#p114959
    definitions["path.pathdepth.total"] = path.depth_total + 1
    definitions["path.pathdepth.diffuse"] = path.depth_diffuse + 1
    definitions["path.pathdepth.glossy"] = path.depth_glossy + 1
    definitions["path.pathdepth.specular"] = path.depth_specular


def _convert_filesaver(scene, definitions, luxcore_engine):
    config = scene.luxcore.config

    filesaver_path = config.filesaver_path
    output_path = utils.get_abspath(filesaver_path, must_exist=True, must_be_existing_dir=True)

    blend_name = bpy.path.basename(bpy.context.blend_data.filepath)
    blend_name = os.path.splitext(blend_name)[0]  # remove ".blend"

    if not blend_name:
        blend_name = "Untitled"

    dir_name = blend_name + "_LuxCore"
    frame_name = "%05d" % scene.frame_current

    # If we have multiple render layers, we append the layer name
    if len(scene.render.layers) > 1:
        render_layer = utils.get_current_render_layer(scene)
        frame_name += "_" + render_layer.name

    if config.filesaver_format == "BIN":
        # For binary format, the frame number is used as file name instead of directory name
        frame_name += ".bcf"
        output_path = os.path.join(output_path, dir_name)
    else:
        # For text format, we use the frame number as name for a subfolder
        output_path = os.path.join(output_path, dir_name, frame_name)

    if not os.path.exists(output_path):
        # https://stackoverflow.com/a/273227
        try:
            os.makedirs(output_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    if config.filesaver_format == "BIN":
        definitions["filesaver.filename"] = os.path.join(output_path, frame_name)
    else:
        # Text format
        definitions["filesaver.directory"] = output_path

    definitions["filesaver.format"] = config.filesaver_format
    definitions["renderengine.type"] = "FILESAVER"
    definitions["filesaver.renderengine.type"] = luxcore_engine


def _convert_seed(scene, definitions):
    config = scene.luxcore.config

    if config.use_animated_seed:
        # frame_current can be 0, but not negative, while LuxCore seed can only be > 1
        seed = scene.frame_current + 1
    else:
        seed = config.seed

    definitions["renderengine.seed"] = seed


def _convert_metropolis_settings(definitions, config):
    definitions["sampler.metropolis.largesteprate"] = config.metropolis_largesteprate / 100
    definitions["sampler.metropolis.maxconsecutivereject"] = config.metropolis_maxconsecutivereject
    definitions["sampler.metropolis.imagemutationrate"] = config.metropolis_imagemutationrate / 100
