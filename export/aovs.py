from ..bin import pyluxcore
from .. import utils
from .imagepipeline import use_backgroundimage

# set of channels that don"t use an HDR format
LDR_CHANNELS = {
    "RGB_IMAGEPIPELINE", "RGBA_IMAGEPIPELINE", "ALPHA", "MATERIAL_ID", "OBJECT_ID",
    "DIRECT_SHADOW_MASK", "INDIRECT_SHADOW_MASK", "MATERIAL_ID_MASK"
}


# Exported in config export
def convert(scene, context=None):
    if scene.camera is None:
        # Can not work without a camera
        return pyluxcore.Properties()

    try:
        prefix = "film.outputs."
        definitions = {}

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

        # Reset the index
        _add_output.index = 0

        # This output is always defined
        _add_output(definitions, "RGB_IMAGEPIPELINE")

        if use_transparent_film:
            _add_output(definitions, "RGBA_IMAGEPIPELINE")

        # AOVs
        if (final and aovs.alpha) or use_transparent_film or use_backgroundimage(context, scene):
            _add_output(definitions, "ALPHA")
        if (final and aovs.depth) or pipeline.mist.enabled:
            _add_output(definitions, "DEPTH")
        if (final and aovs.irradiance) or pipeline.contour_lines.enabled:
            _add_output(definitions, "IRRADIANCE")

        # These AOVs only make sense in final renders
        if final:
            if aovs.rgb:
                _add_output(definitions, "RGB")
            if aovs.rgba:
                _add_output(definitions, "RGBA")
            if aovs.material_id:
                _add_output(definitions, "MATERIAL_ID")
            if aovs.object_id:
                _add_output(definitions, "OBJECT_ID")
            if aovs.emission:
                _add_output(definitions, "EMISSION")
            if aovs.direct_diffuse:
                _add_output(definitions, "DIRECT_DIFFUSE")
            if aovs.direct_glossy:
                _add_output(definitions, "DIRECT_GLOSSY")
            if aovs.indirect_diffuse:
                _add_output(definitions, "INDIRECT_DIFFUSE")
            if aovs.indirect_glossy:
                _add_output(definitions, "INDIRECT_GLOSSY")
            if aovs.indirect_specular:
                _add_output(definitions, "INDIRECT_SPECULAR")
            if aovs.position:
                _add_output(definitions, "POSITION")
            if aovs.shading_normal:
                _add_output(definitions, "SHADING_NORMAL")
            if aovs.geometry_normal:
                _add_output(definitions, "GEOMETRY_NORMAL")
            if aovs.uv:
                _add_output(definitions, "UV")
            if aovs.direct_shadow_mask:
                _add_output(definitions, "DIRECT_SHADOW_MASK")
            if aovs.indirect_shadow_mask:
                _add_output(definitions, "INDIRECT_SHADOW_MASK")
            if aovs.raycount:
                _add_output(definitions, "RAYCOUNT")
            if aovs.samplecount:
                _add_output(definitions, "SAMPLECOUNT")
            if aovs.convergence:
                _add_output(definitions, "CONVERGENCE")

        return utils.create_props(prefix, definitions)
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
def _add_output(definitions, output_type_str, index=0):
    definitions[str(index) + ".type"] = output_type_str

    extension = ".png" if output_type_str in LDR_CHANNELS else ".exr"
    definitions[str(index) + ".filename"] = output_type_str + extension

    return index + 1
