from collections import OrderedDict
from ..bin import pyluxcore
from .. import utils
from .image import ImageExporter


def convert(scene, context=None, index=0):
    try:
        prefix = "film.imagepipelines.%d." % index
        definitions = OrderedDict()

        if not utils.is_valid_camera(scene.camera):
            # Can not work without a camera
            _fallback(definitions)
            return utils.create_props(prefix, definitions)

        convert_defs(context, scene, definitions, 0)

        return utils.create_props(prefix, definitions)
    except Exception as error:
        import traceback
        traceback.print_exc()
        msg = 'Imagepipeline: %s' % error
        scene.luxcore.errorlog.add_warning(msg)
        return pyluxcore.Properties()


def convert_defs(context, scene, definitions, plugin_index, define_radiancescales=True):
    pipeline = scene.camera.data.luxcore.imagepipeline
    use_filesaver = utils.use_filesaver(context, scene)
    # Start index of plugins. Some AOVs prepend their own plugins.
    index = plugin_index

    # Make sure the imagepipeline does nothing when no plugins are enabled
    definitions[str(index) + ".type"] = "NOP"
    index += 1

    if pipeline.tonemapper.enabled:
        index = convert_tonemapper(definitions, index, pipeline.tonemapper)

    # Note: Blender expects the alpha to be NOT premultiplied, so we only
    # premultiply it when the backgroundimage plugin is used
    if use_backgroundimage(context, scene):
        index = _premul_alpha(definitions, index)

    if use_backgroundimage(context, scene):
        index = _backgroundimage(definitions, index, pipeline.backgroundimage, scene)

    if pipeline.mist.enabled:
        index = _mist(definitions, index, pipeline.mist, scene)

    if pipeline.bloom.enabled:
        index = _bloom(definitions, index, pipeline.bloom)

    if pipeline.coloraberration.enabled:
        index = _coloraberration(definitions, index, pipeline.coloraberration)

    if pipeline.vignetting.enabled:
        index = _vignetting(definitions, index, pipeline.vignetting)

    if pipeline.camera_response_func.enabled:
        index = _camera_response_func(definitions, index, pipeline.camera_response_func, scene)

    if pipeline.contour_lines.enabled:
        index = _contour_lines(definitions, index, pipeline.contour_lines)

    if use_filesaver:
        # Needs gamma correction (Blender applies it for us,
        # but now we export for luxcoreui)
        index = _gamma(definitions, index)

    if define_radiancescales:
        _lightgroups(definitions, scene)
    return index


def use_backgroundimage(context, scene):
    viewport_in_camera_view = context and context.region_data.view_perspective == "CAMERA"
    final_render = not context
    pipeline = scene.camera.data.luxcore.imagepipeline
    return pipeline.backgroundimage.enabled and (final_render or viewport_in_camera_view)


def _fallback(definitions):
    """
    Fallback imagepipeline if no camera is in the scene
    """
    index = 0
    definitions[str(index) + ".type"] = "NOP"
    index += 1
    definitions[str(index) + ".type"] = "TONEMAP_AUTOLINEAR"
    index += 1
    # The result of autolinear looks too bright in Blender.
    # Apply the default scale of 0.5 that is also the default in the camera settings
    definitions[str(index) + ".type"] = "TONEMAP_LINEAR"
    definitions[str(index) + ".scale"] = 0.5


def convert_tonemapper(definitions, index, tonemapper):
    # If "Auto Brightness" is enabled, put an autolinear tonemapper
    # in front of the linear tonemapper
    if tonemapper.type == "TONEMAP_LINEAR" and tonemapper.use_autolinear:
        definitions[str(index) + ".type"] = "TONEMAP_AUTOLINEAR"
        index += 1

    # Main tonemapper
    definitions[str(index) + ".type"] = tonemapper.type

    if tonemapper.type == "TONEMAP_LINEAR":
        definitions[str(index) + ".scale"] = tonemapper.linear_scale
    elif tonemapper.type == "TONEMAP_REINHARD02":
        definitions[str(index) + ".prescale"] = tonemapper.reinhard_prescale
        definitions[str(index) + ".postscale"] = tonemapper.reinhard_postscale
        definitions[str(index) + ".burn"] = tonemapper.reinhard_burn
    elif tonemapper.type == "TONEMAP_LUXLINEAR":
        definitions[str(index) + ".fstop"] = tonemapper.fstop
        definitions[str(index) + ".exposure"] = tonemapper.exposure
        definitions[str(index) + ".sensitivity"] = tonemapper.sensitivity

    return index + 1


def _premul_alpha(definitions, index):
    definitions[str(index) + ".type"] = "PREMULTIPLY_ALPHA"
    return index + 1


def _backgroundimage(definitions, index, backgroundimage, scene):
    if backgroundimage.image is None:
        return index

    try:
        filepath = ImageExporter.export(backgroundimage.image,
                                        backgroundimage.image_user,
                                        scene)
    except OSError as error:
        msg = "Imagepipeline: %s" % error
        scene.luxcore.errorlog.add_warning(msg)
        # Skip this plugin
        return index

    definitions[str(index) + ".type"] = "BACKGROUND_IMG"
    definitions[str(index) + ".file"] = filepath
    definitions[str(index) + ".gamma"] = backgroundimage.gamma
    definitions[str(index) + ".storage"] = backgroundimage.storage
    return index + 1


def _mist(definitions, index, mist, scene):
    worldscale = utils.get_worldscale(scene, as_scalematrix=False)

    definitions[str(index) + ".type"] = "MIST"
    definitions[str(index) + ".color"] = list(mist.color)
    definitions[str(index) + ".amount"] = mist.amount / 100
    definitions[str(index) + ".startdistance"] = mist.start_distance * worldscale
    definitions[str(index) + ".enddistance"] = mist.end_distance * worldscale
    definitions[str(index) + ".excludebackground"] = mist.exclude_background
    return index + 1


def _bloom(definitions, index, bloom):
    definitions[str(index) + ".type"] = "BLOOM"
    definitions[str(index) + ".radius"] = bloom.radius / 100
    definitions[str(index) + ".weight"] = bloom.weight / 100
    return index + 1


def _coloraberration(definitions, index, coloraberration):
    definitions[str(index) + ".type"] = "COLOR_ABERRATION"
    definitions[str(index) + ".amount"] = coloraberration.amount / 100
    return index + 1


def _vignetting(definitions, index, vignetting):
    definitions[str(index) + ".type"] = "VIGNETTING"
    definitions[str(index) + ".scale"] = vignetting.scale / 100
    return index + 1


def _camera_response_func(definitions, index, camera_response_func, scene):
    if camera_response_func.type == "PRESET":
        name = camera_response_func.preset
    elif camera_response_func.type == "FILE":
        try:
            library = scene.camera.data.library
            name = utils.get_abspath(camera_response_func.file, library,
                                     must_exist=True, must_be_existing_file=True)
        except OSError as error:
            # Make the error message more precise
            scene.luxcore.errorlog.add_warning('Could not find .crf file at path "%s" (%s)'
                                               % (camera_response_func.file, error))
            name = None
    else:
        raise NotImplementedError("Unknown crf type: " + camera_response_func.type)

    # Note: preset or file are empty strings until the user selects something
    if name:
        definitions[str(index) + ".type"] = "CAMERA_RESPONSE_FUNC"
        definitions[str(index) + ".name"] = name
        return index + 1
    else:
        return index


def _contour_lines(definitions, index, contour_lines):
    definitions[str(index) + ".type"] = "CONTOUR_LINES"
    definitions[str(index) + ".range"] = contour_lines.contour_range
    definitions[str(index) + ".scale"] = contour_lines.scale
    definitions[str(index) + ".steps"] = contour_lines.steps
    definitions[str(index) + ".zerogridsize"] = contour_lines.zero_grid_size
    return index + 1


def _gamma(definitions, index):
    definitions[str(index) + ".type"] = "GAMMA_CORRECTION"
    definitions[str(index) + ".value"] = 2.2
    return index + 1


def _lightgroups(definitions, scene):
    lightgroups = scene.luxcore.lightgroups

    _lightgroup(definitions, lightgroups.default, 0)

    for i, group in enumerate(lightgroups.custom):
        # +1 to group_id because default group is id 0, but not in the list
        group_id = i + 1
        _lightgroup(definitions, group, group_id)


def _lightgroup(definitions, group, group_id):
    prefix = "radiancescales." + str(group_id) + "."
    definitions[prefix + "enabled"] = group.enabled
    definitions[prefix + "globalscale"] = group.gain

    if group.use_rgb_gain:
        definitions[prefix + "rgbscale"] = list(group.rgb_gain)

    if group.use_temperature:
        definitions[prefix + "temperature"] = group.temperature
