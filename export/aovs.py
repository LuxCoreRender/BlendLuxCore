from collections import OrderedDict
from ..bin import pyluxcore
from .. import utils
from . import imagepipeline
from .imagepipeline import use_backgroundimage

# set of channels that don"t use an HDR format
LDR_CHANNELS = {
    "RGB_IMAGEPIPELINE", "RGBA_IMAGEPIPELINE", "ALPHA", "MATERIAL_ID", "MATERIAL_ID_COLOR",
    "OBJECT_ID", "DIRECT_SHADOW_MASK", "INDIRECT_SHADOW_MASK", "MATERIAL_ID_MASK"
}

# set of channels that should be tonemapped the same way as the RGB_IMAGEPIPELINE
NEED_TONEMAPPING = {
    "EMISSION", "RADIANCE_GROUP",
    "DIRECT_DIFFUSE", "DIRECT_GLOSSY",
    "INDIRECT_DIFFUSE", "INDIRECT_GLOSSY", "INDIRECT_SPECULAR",
    "BY_MATERIAL_ID", "BY_OBJECT_ID",
}


# Exported in config export
def convert(exporter, scene, context=None, engine=None):
    try:
        prefix = "film.outputs."
        # Ordered because we sometimes need to read these for debugging
        definitions = OrderedDict()
        # Reset the output index
        _add_output.index = 0

        # If we have a context, we are in viewport render.
        # If engine.is_preview, we are in material preview. Both don't need AOVs.
        final = not context and not (engine and engine.is_preview)

        # Can not work without a camera
        if not utils.is_valid_camera(scene.camera):
            # However, viewport denoising should be possible even without camera
            if not final and scene.luxcore.viewport.denoise:
                _add_output(definitions, "ALBEDO")
                _add_output(definitions, "AVG_SHADING_NORMAL")
            return utils.create_props(prefix, definitions)

        pipeline = scene.camera.data.luxcore.imagepipeline
        denoiser = scene.luxcore.denoiser

        if final:
            # This is the layer that is currently being exported, not the active layer in the UI!
            current_layer = utils.get_current_render_layer(scene)
            aovs = current_layer.luxcore.aovs
        else:
            # AOVs should not be accessed in viewport render
            # (they are a render layer property and those are not evaluated for viewport)
            aovs = None

        use_transparent_film = pipeline.transparent_film and not utils.use_filesaver(context, scene)

        # Some AOVs need tonemapping with a custom imagepipeline
        pipeline_index = 0

        # This output is always defined
        _add_output(definitions, "RGB_IMAGEPIPELINE", pipeline_index)

        if use_transparent_film:
            _add_output(definitions, "RGBA_IMAGEPIPELINE", pipeline_index)

        pipeline_index += 1
        add_OIDN_AOVs = ((final and denoiser.enabled and denoiser.type == "OIDN")
                         or (not final and scene.luxcore.viewport.denoise))

        # AOVs
        if (final and aovs.alpha) or use_transparent_film or use_backgroundimage(context, scene):
            _add_output(definitions, "ALPHA")
        if (final and aovs.depth) or pipeline.mist.enabled:
            _add_output(definitions, "DEPTH")
        if (final and aovs.irradiance) or pipeline.contour_lines.enabled:
            _add_output(definitions, "IRRADIANCE")
        if (final and aovs.albedo) or add_OIDN_AOVs:
            _add_output(definitions, "ALBEDO")
        if (final and aovs.avg_shading_normal) or add_OIDN_AOVs:
            _add_output(definitions, "AVG_SHADING_NORMAL")

        pipeline_props = pyluxcore.Properties()

        # These AOVs only make sense in final renders
        if final:
            for output_name, output_type in pyluxcore.FilmOutputType.names.items():
                if output_name in {"RGB_IMAGEPIPELINE", "RGBA_IMAGEPIPELINE", "ALPHA", "DEPTH",
                                   "IRRADIANCE", "ALBEDO", "AVG_SHADING_NORMAL"}:
                    # We already checked these
                    continue

                # Check if AOV is enabled by user
                if getattr(aovs, output_name.lower(), False):
                    _add_output(definitions, output_name)

                    if output_name in NEED_TONEMAPPING:
                        pipeline_index = _make_imagepipeline(pipeline_props, context, scene, output_name,
                                                             pipeline_index, definitions, engine)

            # Light groups
            if exporter.lightgroup_cache == {0}:
                # Only the default lightgroup in the cache, it doesn't make sense to export lightgroups
                exporter.lightgroup_cache.clear()

            for group_id in exporter.lightgroup_cache:
                output_name = "RADIANCE_GROUP"
                # I don't think we need this output because we define an imagepipeline output anyway
                # _add_output(definitions, output_name, output_id=group_id)
                pipeline_index = _make_imagepipeline(pipeline_props, context, scene, output_name,
                                                     pipeline_index, definitions, engine,
                                                     group_id, exporter.lightgroup_cache)

            if not any([group.enabled for group in scene.luxcore.lightgroups.get_all_groups()]):
                scene.luxcore.errorlog.add_warning("All light groups are disabled.")

            # Denoiser imagepipeline
            if scene.luxcore.denoiser.enabled:
                pipeline_index = _make_denoiser_imagepipeline(context, scene, pipeline_props, engine,
                                                              pipeline_index, definitions)

        props = utils.create_props(prefix, definitions)
        props.Set(pipeline_props)

        return props
    except Exception as error:
        import traceback
        traceback.print_exc()
        msg = "AOVs: %s" % error
        scene.luxcore.errorlog.add_warning(msg)
        return pyluxcore.Properties()


def count_index(func):
    """
    A decorator that increments an index each time the decorated function is called.
    It also passes the index as a keyword argument to the function.
    """
    def wrapper(*args, **kwargs):
        kwargs["index"] = wrapper.index
        wrapper.index += 1
        return func(*args, **kwargs)
    wrapper.index = 0
    return wrapper


@count_index
def _add_output(definitions, output_type_str, pipeline_index=-1, output_id=-1, index=0):
    definitions[str(index) + ".type"] = output_type_str

    filename = output_type_str

    if pipeline_index != -1:
        definitions[str(index) + ".index"] = pipeline_index
        filename += "_" + str(pipeline_index)

    extension = ".png" if output_type_str in LDR_CHANNELS else ".exr"
    definitions[str(index) + ".filename"] = filename + extension

    if output_id != -1:
        definitions[str(index) + ".id"] = output_id

    return index + 1


def _make_imagepipeline(props, context, scene, output_name, pipeline_index, output_definitions, engine,
                        output_id=-1, lightgroup_ids=set()):
    tonemapper = scene.camera.data.luxcore.imagepipeline.tonemapper

    if not tonemapper.enabled:
        return pipeline_index

    if tonemapper.is_automatic():
        # We can not work with an automatic tonemapper because
        # every AOV will differ in brightness
        msg = "Use a non-automatic tonemapper to get tonemapped AOVs"
        scene.luxcore.errorlog.add_warning(msg)
        return pipeline_index

    prefix = "film.imagepipelines." + str(pipeline_index) + "."
    definitions = OrderedDict()
    index = 0

    if output_name == "RADIANCE_GROUP":
        for group_id in lightgroup_ids:
            # Disable all light groups except one per imagepipeline
            definitions["radiancescales." + str(group_id) + ".enabled"] = (output_id == group_id)
    else:
        definitions[str(index) + ".type"] = "OUTPUT_SWITCHER"
        definitions[str(index) + ".channel"] = output_name
        if output_id != -1:
            definitions[str(index) + ".index"] = output_id
        index += 1

    # Define the rest of the imagepipeline.
    # When defining a lightgroup pipeline, do not override the radiancescales we defined above.
    define_radiancescales = not lightgroup_ids
    index = imagepipeline.convert_defs(context, scene, definitions, index, define_radiancescales)

    props.Set(utils.create_props(prefix, definitions))
    _add_output(output_definitions, "RGB_IMAGEPIPELINE", pipeline_index)

    # Register in the engine so we know the correct index
    # when we draw the framebuffer during rendering
    key = output_name
    if output_id != -1:
        key += str(output_id)
    engine.aov_imagepipelines[key] = pipeline_index

    return pipeline_index + 1


def get_denoiser_imgpipeline_props(context, scene, pipeline_index):
    prefix = "film.imagepipelines." + str(pipeline_index) + "."
    definitions = OrderedDict()
    index = 0

    if scene.luxcore.denoiser.type == "BCD":
        index = get_BCD_props(definitions, scene, index)
    elif scene.luxcore.denoiser.type == "OIDN":
        index = get_OIDN_props(definitions, index)

    index = imagepipeline.convert_defs(context, scene, definitions, index)

    return utils.create_props(prefix, definitions)


def get_BCD_props(definitions, scene, index):
    denoiser = scene.luxcore.denoiser
    definitions[str(index) + ".type"] = "BCD_DENOISER"
    definitions[str(index) + ".scales"] = denoiser.scales
    definitions[str(index) + ".histdistthresh"] = denoiser.hist_dist_thresh
    definitions[str(index) + ".patchradius"] = denoiser.patch_radius
    definitions[str(index) + ".searchwindowradius"] = denoiser.search_window_radius
    definitions[str(index) + ".filterspikes"] = denoiser.filter_spikes
    if scene.render.threads_mode == "FIXED":
        definitions[str(index) + ".threadcount"] = scene.render.threads
    config = scene.luxcore.config
    if config.engine == "PATH" and config.use_tiles:
        epsilon = 0.1
        aa = config.tile.path_sampling_aa_size
        definitions[str(index) + ".warmupspp"] = aa ** 2 - epsilon
    return index + 1


def get_OIDN_props(definitions, index):
    definitions[str(index) + ".type"] = "INTEL_OIDN"
    return index + 1


def _make_denoiser_imagepipeline(context, scene, props, engine, pipeline_index, output_definitions):
    props.Set(get_denoiser_imgpipeline_props(context, scene, pipeline_index))
    _add_output(output_definitions, "RGB_IMAGEPIPELINE", pipeline_index)
    engine.aov_imagepipelines["DENOISED"] = pipeline_index
    return pipeline_index + 1
