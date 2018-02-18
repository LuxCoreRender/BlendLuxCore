from ..bin import pyluxcore
from .. import utils
from .image import ImageExporter


def convert(scene, context=None):
    try:
        prefix = "film.imagepipeline."
        definitions = {}

        if scene.camera is None:
            # Can not work without a camera
            return pyluxcore.Properties()

        pipeline = scene.camera.data.luxcore.imagepipeline
        use_filesaver = utils.use_filesaver(context, scene)
        # Plugin index counter
        index = 0

        # Make sure the imagepipeline does nothing when no plugins are enabled
        definitions[str(index) + ".type"] = "NOP"
        index += 1

        if pipeline.tonemapper.enabled:
            index = _tonemapper(definitions, index, pipeline.tonemapper)

        if pipeline.transparent_film and not use_filesaver:
            # Blender expects premultiplied alpha, luxcoreui does not
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

        # TODO irradiance contour lines

        if use_filesaver:
            # Needs gamma correction (Blender applies it for us,
            # but now we export for luxcoreui)
            index = _gamma(definitions, index)

        return utils.create_props(prefix, definitions)
    except Exception as error:
        msg = 'Imagepipeline: %s' % error
        scene.luxcore.errorlog.add_warning(msg)
        return pyluxcore.Properties()


def use_backgroundimage(context, scene):
    viewport_in_camera_view = context and context.region_data.view_perspective == "CAMERA"
    final_render = not context
    pipeline = scene.camera.data.luxcore.imagepipeline
    return pipeline.backgroundimage.enabled and (final_render or viewport_in_camera_view)


def _tonemapper(definitions, index, tonemapper):
    # If "Auto Brightness" is enabled, put an autolinear tonemapper
    # in front of the linear tonemapper
    if tonemapper.type == "TONEMAP_LINEAR" and tonemapper.use_autolinear:
        definitions[str(index) + ".type"] = "TONEMAP_AUTOLINEAR"
        index += 1

    # Main tonemapper
    definitions[str(index) + ".type"] = tonemapper.type

    if tonemapper.type == 'TONEMAP_LINEAR':
        definitions[str(index) + ".scale"] = tonemapper.linear_scale
    elif tonemapper.type == 'TONEMAP_REINHARD02':
        definitions[str(index) + ".prescale"] = tonemapper.reinhard_prescale
        definitions[str(index) + ".postscale"] = tonemapper.reinhard_postscale
        definitions[str(index) + ".burn"] = tonemapper.reinhard_burn
    elif tonemapper.type == 'TONEMAP_LUXLINEAR':
        definitions[str(index) + ".fstop"] = tonemapper.fstop
        definitions[str(index) + ".exposure"] = tonemapper.exposure
        definitions[str(index) + ".sensitivity"] = tonemapper.sensitivity

    return index + 1


def _premul_alpha(definitions, index):
    definitions[str(index) + ".type"] = "PREMULTIPLY_ALPHA"
    return index + 1


def _backgroundimage(definitions, index, backgroundimage, scene):
    try:
        filepath = ImageExporter.export(backgroundimage.image)
    except OSError as error:
        msg = 'Imagepipeline: %s' % error
        scene.luxcore.errorlog.add_warning(msg)
        # Skip this plugin
        return index

    definitions[str(index) + ".type"] = "BACKGROUND_IMG"
    definitions[str(index) + ".file"] = filepath
    definitions[str(index) + ".gamma"] = backgroundimage.gamma
    definitions[str(index) + ".storage"] = "byte"
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


def _gamma(definitions, index):
    definitions[str(index) + ".type"] = "GAMMA_CORRECTION"
    definitions[str(index) + ".value"] = 2.2
    return index + 1
