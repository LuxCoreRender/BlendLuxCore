import os
import errno
import bpy
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
            "film.filter.type": "BLACKMANHARRIS" if config.use_filter else "NONE",
            "film.filter.width": config.filter_width,

            "periodicsave.resumerendering.period": 60,
            "periodicsave.resumerendering.filename": "test.rsm",
        })

        # Resume rendering file (only in final render)
        if context is None and config.save_resumefile:
            _convert_resumefile(scene, definitions)

        # FILESAVER engine (only in final render)
        use_filesaver = context is None and config.use_filesaver
        if use_filesaver:
            _convert_filesaver(scene, definitions, engine)

        # CPU thread settings (we use the properties from Blender here)
        if scene.render.threads_mode == "FIXED":
            definitions["native.threads.count"] = scene.render.threads

        # TODO: remove this once we properly implement the imagepipeline
        # very crude imagepipeline, just for now so final matches viewport
        definitions["film.outputs.1.type"] = "RGB_IMAGEPIPELINE"
        definitions["film.outputs.1.filename"] = "RGB_IMAGEPIPELINE.png"
        definitions["film.imagepipeline.0.type"] = "TONEMAP_AUTOLINEAR"
        definitions["film.imagepipeline.1.type"] = "TONEMAP_LINEAR"
        definitions["film.imagepipeline.1.scale"] = 1 / 2.25
        if use_filesaver:
            # Needs gamma correction
            definitions["film.imagepipeline.2.type"] = "GAMMA_CORRECTION"
            definitions["film.imagepipeline.2.value"] = 2.2

        return utils.create_props(prefix, definitions)
    except Exception as error:
        msg = 'Config: %s' % error
        scene.luxcore.errorlog.add_warning(msg)
        return pyluxcore.Properties()


def _convert_path(config, definitions):
    path = config.path
    # Note that for non-specular paths +1 is added to the path depth.
    # For details see http://www.luxrender.net/forum/viewtopic.php?f=11&t=11101&start=390#p114959
    definitions["path.pathdepth.total"] = path.depth_total + 1
    definitions["path.pathdepth.diffuse"] = path.depth_diffuse + 1
    definitions["path.pathdepth.glossy"] = path.depth_glossy + 1
    definitions["path.pathdepth.specular"] = path.depth_specular
    # TODO path.forceblackbackground.enable (if film is transparent)

    if path.use_clamping:
        definitions["path.clamping.variance.maxvalue"] = path.clamping


def _prepare_output_dir(scene):
    """
    Makes sure that the user-specified output path exists.
    This function can be called multiple times.

    Creates a subdirectory structure within, using the following scheme:
    <.blend file name>_LuxCore/<frame number>/
    E.g. output_path/Untitled_LuxCore/00001/

    Returns: the output path, a suggested base name for files.
    If the user-specified output path does not exist, an OSError is raised
    """

    output_path = utils.get_abspath(scene.render.filepath, must_exist=True)
    if output_path is None:
        raise OSError('Not a valid output path: "%s"' % scene.render.filepath)

    blend_name = bpy.path.basename(bpy.context.blend_data.filepath)
    blend_name = os.path.splitext(blend_name)[0]  # remove ".blend"
    if not blend_name:
        blend_name = "Untitled"

    dir_name = blend_name + "_LuxCore"

    frame_name = "%05d" % scene.frame_current

    # example path: "output_path/Untitled_LuxCore/00001/"
    output_path = os.path.join(output_path, dir_name, frame_name)

    # Create the output path
    if not os.path.exists(output_path):
        # https://stackoverflow.com/a/273227
        try:
            os.makedirs(output_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    # Basename for all kinds of output files
    output_file_basename = blend_name + "_" + frame_name

    return output_path, output_file_basename


def _convert_filesaver(scene, definitions, engine):
    config = scene.luxcore.config

    output_path, basename = _prepare_output_dir(scene)

    if config.filesaver_format == "BIN":
        definitions["filesaver.filename"] = os.path.join(output_path, basename + ".bcf")
    else:
        # Text format
        definitions["filesaver.directory"] = output_path

    definitions["filesaver.format"] = config.filesaver_format
    definitions["renderengine.type"] = "FILESAVER"
    definitions["filesaver.renderengine.type"] = engine


def _convert_resumefile(scene, definitions):
    config = scene.luxcore.config

    output_path, basename = _prepare_output_dir(scene)
    filename = os.path.join(output_path, basename + ".rsm")

    if os.path.isfile(filename):
        # File exists
        msg = 'Film resume file already exists: "%s"' % filename
        scene.luxcore.errorlog.add_warning(msg)

        # Find a new name by appending a number
        i = 0
        while True:
            i += 1
            new_name = "%s_%02d" % (filename, i)
            if not os.path.isfile(new_name):
                filename = new_name
                break

    definitions["periodicsave.resumerendering.period"] = config.resumefile_save_interval
    definitions["periodicsave.resumerendering.filename"] = filename
