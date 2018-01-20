import bpy
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

        index = _tonemapper(definitions, index, pipeline)

        if use_filesaver:
            # Needs gamma correction (Blender applies it for us,
            # but now we export for luxcoreui)
            index = _gamma(definitions, index)

        return utils.create_props(prefix, definitions)
    except Exception as error:
        msg = 'Imagepipeline: %s' % error
        scene.luxcore.errorlog.add_warning(msg)
        return pyluxcore.Properties()


def _tonemapper(definitions, index, pipeline):
    # If "Auto Brightness" is enabled, put an autolinear tonemapper
    # in front of the linear tonemapper
    if pipeline.tonemapper == "TONEMAP_LINEAR" and pipeline.use_autolinear:
        definitions[str(index) + ".type"] = "TONEMAP_AUTOLINEAR"
        index += 1

    # Tonemapper
    definitions[str(index) + ".type"] = pipeline.tonemapper

    if pipeline.tonemapper == 'TONEMAP_LINEAR':
        definitions[str(index) + ".scale"] = pipeline.linear_scale

    elif pipeline.tonemapper == 'TONEMAP_REINHARD02':
        definitions[str(index) + ".prescale"] = pipeline.reinhard_prescale
        definitions[str(index) + ".postscale"] = pipeline.reinhard_postscale
        definitions[str(index) + ".burn"] = pipeline.reinhard_burn

    elif pipeline.tonemapper == 'TONEMAP_LUXLINEAR':
        definitions[str(index) + ".fstop"] = pipeline.fstop
        definitions[str(index) + ".exposure"] = pipeline.exposure
        definitions[str(index) + ".sensitivity"] = pipeline.sensitivity

    return index + 1


def _gamma(definitions, index):
    definitions[str(index) + ".type"] = "GAMMA_CORRECTION"
    definitions[str(index) + ".value"] = 2.2
    return index + 1
