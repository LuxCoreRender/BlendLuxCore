import os
import errno
from math import degrees
import bpy
from collections import OrderedDict
from ..bin import pyluxcore
from .. import utils
from . import aovs
from .imagepipeline import use_backgroundimage


def convert(exporter, scene, context=None, engine=None):
    try:
        prefix = ""
        # We collect the properties in this dictionary (ordered because we sometimes
        # need to read them for debugging).
        # The dictionary is converted to pyluxcore.Properties() in the return statement.
        definitions = OrderedDict()

        # See properties/config.py
        config = scene.luxcore.config
        width, height = utils.calc_filmsize(scene, context)
        use_bidir_in_viewport = config.engine == "BIDIR" and scene.luxcore.viewport.use_bidir

        if context and not use_bidir_in_viewport:
            # Viewport render
            luxcore_engine, sampler = _convert_viewport_engine(scene, definitions, config)
        else:
            # Final render
            luxcore_engine, sampler = _convert_final_engine(scene, definitions, config)

        if luxcore_engine == "BIDIRCPU" and scene.luxcore.denoiser.enabled:
            filter_type = "NONE"
        else:
            filter_type = config.filter

        # Common properties that should be set regardless of engine configuration.
        definitions.update({
            "renderengine.type": luxcore_engine,
            "sampler.type": sampler,
            "film.width": width,
            "film.height": height,
            "film.filter.type": filter_type,
            "film.filter.width": config.filter_width,
            "lightstrategy.type": config.light_strategy,
            "scene.epsilon.min": config.min_epsilon,
            "scene.epsilon.max": config.max_epsilon,
        })

        if config.film_opencl_enable and config.film_opencl_device != "none":
            definitions["film.opencl.enable"] = True
            definitions["film.opencl.device"] = int(config.film_opencl_device)
        else:
            definitions["film.opencl.enable"] = False

        if config.light_strategy == "DLS_CACHE":
            _convert_dlscache_settings(scene, definitions, config)

        if config.photongi.enabled:
            _convert_photongi_settings(context, scene, definitions, config)

        if config.path.use_clamping:
            definitions["path.clamping.variance.maxvalue"] = config.path.clamping

        # Filter
        if config.filter == "GAUSSIAN":
            definitions["film.filter.gaussian.alpha"] = config.gaussian_alpha

        use_filesaver = utils.use_filesaver(context, scene)

        # Transparent film settings
        black_background = False
        if utils.is_valid_camera(scene.camera):
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
        aov_props = aovs.convert(exporter, scene, context, engine)
        config_props.Set(aov_props)

        return config_props
    except Exception as error:
        msg = 'Config: %s' % error
        # Note: Exceptions in the config are critical, we can't render without a config
        scene.luxcore.errorlog.add_error(msg)
        return pyluxcore.Properties()


def _convert_opencl_settings(scene, definitions, is_final_render):
    if scene.luxcore.debug.enabled and scene.luxcore.debug.use_opencl_cpu:
        # This is a mode for debugging OpenCL problems.
        # If the problem shows up in this mode, it is most
        # likely a bug in LuxCore and not an OpenCL compiler bug.
        definitions["opencl.cpu.use"] = True
        definitions["opencl.gpu.use"] = False
        definitions["opencl.native.threads.count"] = 0
    else:
        opencl = scene.luxcore.opencl
        definitions["opencl.cpu.use"] = False
        definitions["opencl.gpu.use"] = True
        definitions["opencl.devices.select"] = opencl.devices_to_selection_string()

        # OpenCL CPU (hybrid render) thread settings. Only enabled in final render.
        if opencl.use_native_cpu and is_final_render:
            # We use the properties from Blender here
            if scene.render.threads_mode == "FIXED":
                # Explicitly set the number of threads
                definitions["opencl.native.threads.count"] = scene.render.threads
            # If no thread count is specified, LuxCore automatically uses all available cores
        else:
            # Disable hybrid rendering
            definitions["opencl.native.threads.count"] = 0


def _convert_viewport_engine(scene, definitions, config):
    _convert_path(config, definitions)

    viewport = scene.luxcore.viewport

    use_cpu = viewport.device == "CPU"
    if not use_cpu and not utils.is_opencl_build():
        msg = "Config: LuxCore was built without OpenCL support, can't use OpenCL engine in viewport"
        scene.luxcore.errorlog.add_warning(msg)
        use_cpu = True

    resolutionreduction = viewport.resolution_reduction if viewport.reduce_resolution_on_edit else 1

    if use_cpu:
        luxcore_engine = "RTPATHCPU"
        sampler = "RTPATHCPUSAMPLER"
        # Size of the blocks right after a scene edit (in pixels)
        definitions["rtpathcpu.zoomphase.size"] = resolutionreduction
        # How to blend new samples over old ones.
        # Set to 0 because otherwise bright pixels (e.g. meshlights) stay blocky for a long time.
        definitions["rtpathcpu.zoomphase.weight"] = 0
    else:
        luxcore_engine = "RTPATHOCL"
        sampler = "TILEPATHSAMPLER"
        # Render a sample every n x n pixels in the first passes.
        # For instance 4x4 then 2x2 and then always 1x1.
        definitions["rtpath.resolutionreduction.preview"] = resolutionreduction
        # Each preview step is rendered for n frames.
        definitions["rtpath.resolutionreduction.step"] = 1
        # Render a sample every n x n pixels, outside the preview phase,
        # in order to reduce the per frame rendering time.
        definitions["rtpath.resolutionreduction"] = 1

        # Enable a bunch of often-used features to minimize the need for kernel recompilations
        enabled_opencl_features = " ".join([
            # Materials
            "MATTE", "ROUGHMATTE", "MATTETRANSLUCENT", "ROUGHMATTETRANSLUCENT",
            "GLOSSY2", "GLOSSYTRANSLUCENT",
            "GLASS", "ARCHGLASS", "ROUGHGLASS",
            "MIRROR", "METAL2",
            "NULLMAT",
            # Material features
            "HAS_BUMPMAPS", "GLOSSY2_ABSORPTION", "GLOSSY2_MULTIBOUNCE",
            # Volumes
            "HOMOGENEOUS_VOL", "CLEAR_VOL",
            # Textures
            "IMAGEMAPS_BYTE_FORMAT", "IMAGEMAPS_HALF_FORMAT",
            "IMAGEMAPS_1xCHANNELS", "IMAGEMAPS_3xCHANNELS",
            # Lights
            "INFINITE", "TRIANGLELIGHT", "SKY2", "SUN", "POINT", "MAPPOINT",
            "SPOTLIGHT", "CONSTANTINFINITE", "PROJECTION", "SHARPDISTANT",
            "DISTANT", "LASER", "SPHERE", "MAPSPHERE",
        ])
        definitions["opencl.code.alwaysenabled"] = enabled_opencl_features
        _convert_opencl_settings(scene, definitions, False)

    return luxcore_engine, sampler


def _convert_final_engine(scene, definitions, config):
    if config.engine == "PATH":
        # Specific settings for PATH and TILEPATH
        _convert_path(config, definitions)

        if config.use_tiles:
            luxcore_engine = "TILEPATH"
            # Tile specific settings
            tile = config.tile

            definitions["tilepath.sampling.aa.size"] = tile.path_sampling_aa_size
            definitions["tile.size"] = tile.size
            definitions["tile.multipass.enable"] = tile.multipass_enable or utils.use_two_tiled_passes(scene)
            thresh = tile.multipass_convtest_threshold
            definitions["tile.multipass.convergencetest.threshold"] = thresh
            thresh_reduct = tile.multipass_convtest_threshold_reduction
            definitions["tile.multipass.convergencetest.threshold.reduction"] = thresh_reduct
            warmup = tile.multipass_convtest_warmup
            definitions["tile.multipass.convergencetest.warmup.count"] = warmup
        else:
            luxcore_engine = "PATH"

        # Add CPU/OCL suffix
        luxcore_engine += config.device

        if config.device == "OCL":
            # OpenCL specific settings
            _convert_opencl_settings(scene, definitions, True)
    else:
        # config.engine == BIDIR
        luxcore_engine = "BIDIRCPU"
        definitions["light.maxdepth"] = config.bidir_light_maxdepth
        definitions["path.maxdepth"] = config.bidir_path_maxdepth

    # Sampler
    if config.engine == "PATH" and config.use_tiles:
        # TILEPATH needs exactly this sampler
        sampler = "TILEPATHSAMPLER"
    else:
        sampler = config.sampler
        adaptive_strength = config.sobol_adaptive_strength
        if adaptive_strength > 0:
            definitions["film.noiseestimation.warmup"] = config.noise_estimation.warmup
            definitions["film.noiseestimation.step"] = config.noise_estimation.step
        definitions["sampler.sobol.adaptive.strength"] = adaptive_strength
        definitions["sampler.random.adaptive.strength"] = adaptive_strength
        _convert_metropolis_settings(definitions, config)

    return luxcore_engine, sampler


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

    blend_name = utils.get_blendfile_name()
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


def _convert_dlscache_settings(scene, definitions, config):
    dls_cache = config.dls_cache
    worldscale = utils.get_worldscale(scene, as_scalematrix=False)
    definitions.update({
        "lightstrategy.entry.radius": 0 if dls_cache.entry_radius_auto else dls_cache.entry_radius * worldscale,
        "lightstrategy.entry.normalangle": degrees(dls_cache.entry_normalangle),
        "lightstrategy.entry.maxpasses": dls_cache.entry_maxpasses,
        "lightstrategy.entry.convergencethreshold": dls_cache.entry_convergencethreshold / 100,
        "lightstrategy.entry.warmupsamples": dls_cache.entry_warmupsamples,
        "lightstrategy.entry.volumes.enable": dls_cache.entry_volumes_enable,

        "lightstrategy.lightthreshold": dls_cache.lightthreshold / 100,
        "lightstrategy.targetcachehitratio": dls_cache.targetcachehitratio / 100,
        "lightstrategy.maxdepth": dls_cache.maxdepth,
        "lightstrategy.maxsamplescount": dls_cache.maxsamplescount,
    })


def _convert_photongi_settings(context, scene, definitions, config):
    photongi = config.photongi
    worldscale = utils.get_worldscale(scene, as_scalematrix=False)

    if photongi.indirect_lookup_radius_auto:
        indirect_radius = 0
    else:
        indirect_radius = photongi.indirect_lookup_radius * worldscale

    if photongi.indirect_haltthreshold_preset == "final":
        indirect_haltthreshold = 0.05
    elif photongi.indirect_haltthreshold_preset == "preview":
        indirect_haltthreshold = 0.15
    elif photongi.indirect_haltthreshold_preset == "custom":
        indirect_haltthreshold = photongi.indirect_haltthreshold_custom / 100
    else:
        raise Exception("Unknown preset mode")

    caustic_radius = photongi.caustic_lookup_radius * worldscale
    caustic_merge_radius_scale = photongi.caustic_merge_radius_scale if photongi.caustic_merge_enabled else 0

    file_path_abs = utils.get_abspath(photongi.file_path, library=scene.library)
    if not os.path.isfile(file_path_abs) and not photongi.save_or_overwrite:
        # Do not save the cache file
        file_path = ""
    else:
        if utils.use_filesaver(context, scene) and photongi.file_path.startswith("//"):
            # It is a relative path and we are using filesaver - don't make it
            # an absolute path, just strip the leading "//"
            file_path = photongi.file_path[2:]
        else:
            file_path = file_path_abs
            if os.path.isfile(file_path) and photongi.save_or_overwrite:
                # To overwrite the file, we first have to delete it, otherwise
                # LuxCore loads the cache from this file
                os.remove(file_path)

    definitions.update({
        "path.photongi.photon.maxcount": round(photongi.photon_maxcount * 1000000),
        "path.photongi.photon.maxdepth": photongi.photon_maxdepth,

        "path.photongi.indirect.enabled": photongi.indirect_enabled,
        "path.photongi.indirect.maxsize": 0,  # Set to 0 to use haltthreshold stop condition
        "path.photongi.indirect.haltthreshold": indirect_haltthreshold,
        "path.photongi.indirect.lookup.radius": indirect_radius,
        "path.photongi.indirect.lookup.normalangle": degrees(photongi.indirect_normalangle),
        "path.photongi.indirect.glossinessusagethreshold": photongi.indirect_glossinessusagethreshold,
        "path.photongi.indirect.usagethresholdscale": photongi.indirect_usagethresholdscale,

        "path.photongi.caustic.enabled": photongi.caustic_enabled,
        "path.photongi.caustic.maxsize": round(photongi.caustic_maxsize * 1000000),
        "path.photongi.caustic.lookup.radius": caustic_radius,
        "path.photongi.caustic.lookup.maxcount": photongi.caustic_lookup_maxcount,
        "path.photongi.caustic.lookup.normalangle": degrees(photongi.caustic_normalangle),
        "path.photongi.caustic.merge.radiusscale": caustic_merge_radius_scale,

        "path.photongi.persistent.file": file_path
    })

    if photongi.debug != "off":
        definitions["path.photongi.debug.type"] = photongi.debug
