from ..bin import pyluxcore
from .. import utils
from .imagepipeline import use_backgroundimage

# set of channels that don"t use an HDR format
LDR_CHANNELS = {
    "RGB_IMAGEPIPELINE", "RGBA_IMAGEPIPELINE", "ALPHA", "MATERIAL_ID", "OBJECT_ID",
    "DIRECT_SHADOW_MASK", "INDIRECT_SHADOW_MASK", "MATERIAL_ID_MASK"
}

# set of channels that should be tonemapped the same way as the RGB_IMAGEPIPELINE
NEED_TONEMAPPING = {
    "EMISSION", "RADIANCE_GROUP",
    "DIRECT_DIFFUSE", "DIRECT_GLOSSY",
    "INDIRECT_DIFFUSE", "INDIRECT_GLOSSY", "INDIRECT_SPECULAR",
    "BY_MATERIAL_ID", "BY_OBJECT_ID",
}


# Exported in config export
def convert(scene, context=None, engine=None):
    try:
        prefix = "film.outputs."
        definitions = {}

        if scene.camera is None:
            # Can not work without a camera
            return pyluxcore.Properties()

        pipeline = scene.camera.data.luxcore.imagepipeline
        final = not context

        if final:
            # This is the layer that is currently being exported, not the active layer in the UI!
            current_layer = utils.get_current_render_layer(scene)
            aovs = current_layer.luxcore.aovs
        else:
            # AOVs should not be accessed in viewport render
            # (they are a render layer property and those are not evaluated for viewport)
            aovs = None

        use_transparent_film = pipeline.transparent_film and not utils.use_filesaver(context, scene)

        # TODO correct filepaths

        # Reset the output index
        _add_output.index = 0

        # Some AOVs need tonemapping with a custom imagepipeline
        pipeline_index = 0

        # This output is always defined
        _add_output(definitions, "RGB_IMAGEPIPELINE", pipeline_index)

        if use_transparent_film:
            _add_output(definitions, "RGBA_IMAGEPIPELINE", pipeline_index)

        pipeline_index += 1

        # AOVs
        if (final and aovs.alpha) or use_transparent_film or use_backgroundimage(context, scene):
            _add_output(definitions, "ALPHA")
        if (final and aovs.depth) or pipeline.mist.enabled:
            _add_output(definitions, "DEPTH")
        if (final and aovs.irradiance) or pipeline.contour_lines.enabled:
            _add_output(definitions, "IRRADIANCE")

        pipeline_props = pyluxcore.Properties()

        # These AOVs only make sense in final renders
        if final:
            for output_name, output_type in pyluxcore.FilmOutputType.names.items():
                if output_name in {"RGB_IMAGEPIPELINE", "RGBA_IMAGEPIPELINE", "ALPHA", "DEPTH", "IRRADIANCE"}:
                    # We already checked these
                    continue

                # Check if AOV is enabled by user
                if getattr(aovs, output_name.lower(), False):
                    _add_output(definitions, output_name)

                    if output_name in NEED_TONEMAPPING:
                        pipeline_index = _make_imagepipeline(pipeline_props, scene, output_name,
                                                             pipeline_index, definitions, engine)

            # Light groups
            lightgroups = scene.luxcore.lightgroups
            # Number of custom groups + default group
            lightgroup_count = len(lightgroups.custom) + 1

            for group_id in range(lightgroup_count):
                output_name = "RADIANCE_GROUP"
                _add_output(definitions, output_name, output_id=group_id)
                pipeline_index = _make_imagepipeline(pipeline_props, scene, output_name,
                                                     pipeline_index, definitions, engine,
                                                     group_id, lightgroup_count)

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


def _make_imagepipeline(props, scene, output_name, pipeline_index, output_definitions, engine,
                        output_id=-1, lightgroup_count=-1):
    # TODO I think we need the full imagepipeline with all plugins here

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
    definitions = {}
    index = 0

    if output_name == "RADIANCE_GROUP":
        for group_id in range(lightgroup_count):
            # Disable all light groups except one per imagepipeline
            definitions["radiancescales." + str(group_id) + ".enabled"] = (output_id == group_id)
    else:
        definitions[str(index) + ".type"] = "OUTPUT_SWITCHER"
        definitions[str(index) + ".channel"] = output_name
        if output_id != -1:
            definitions[str(index) + ".index"] = output_id
        index += 1

    # Tonemapper
    definitions[str(index) + ".type"] = tonemapper.type

    if tonemapper.type == "TONEMAP_LINEAR":
        definitions[str(index) + ".scale"] = tonemapper.linear_scale
    elif tonemapper.type == "TONEMAP_LUXLINEAR":
        definitions[str(index) + ".fstop"] = tonemapper.fstop
        definitions[str(index) + ".exposure"] = tonemapper.exposure
        definitions[str(index) + ".sensitivity"] = tonemapper.sensitivity
    index += 1

    if utils.use_filesaver(None, scene):
        definitions[str(index) + ".type"] = "GAMMA_CORRECTION"
        definitions[str(index) + ".value"] = 2.2
        index += 1

    props.Set(utils.create_props(prefix, definitions))
    _add_output(output_definitions, "RGB_IMAGEPIPELINE", pipeline_index)

    # Register in the engine so we know the correct index
    # when we draw the framebuffer during rendering
    key = output_name
    if output_id != -1:
        key += str(output_id)
    engine.aov_imagepipelines[key] = pipeline_index

    return pipeline_index + 1
