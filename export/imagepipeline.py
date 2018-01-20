from ..bin import pyluxcore
from .. import utils


def convert(scene, context=None):
    try:
        prefix = "film.imagepipeline."
        definitions = {}

        if scene.camera is None:
            # Can not work without a camera
            return pyluxcore.Properties()

        pipeline = scene.camera.data.luxcore.imagepipeline
        use_filesaver = context is None and scene.luxcore.config.use_filesaver
        # Plugin index counter
        index = 0

        # Make sure the imagepipeline does nothing when no plugins are enabled
        definitions[str(index) + ".type"] = "NOP"
        index += 1

        if pipeline.tonemapper.enabled:
            index = _tonemapper(definitions, index, pipeline.tonemapper)

        if pipeline.bloom.enabled:
            index = _bloom(definitions, index, pipeline.bloom)

        if use_filesaver:
            # Needs gamma correction (Blender applies it for us,
            # but now we export for luxcoreui)
            index = _gamma(definitions, index)

        return utils.create_props(prefix, definitions)
    except Exception as error:
        msg = 'Imagepipeline: %s' % error
        scene.luxcore.errorlog.add_warning(msg)
        return pyluxcore.Properties()


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


def _bloom(definitions, index, bloom):
    definitions[str(index) + ".type"] = "BLOOM"
    definitions[str(index) + ".radius"] = bloom.radius / 100
    definitions[str(index) + ".weight"] = bloom.weight / 100
    return index + 1


def _gamma(definitions, index):
    definitions[str(index) + ".type"] = "GAMMA_CORRECTION"
    definitions[str(index) + ".value"] = 2.2
    return index + 1
