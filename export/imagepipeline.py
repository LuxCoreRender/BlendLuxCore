from collections import OrderedDict
import pyluxcore
from .. import utils
from .image import ImageExporter
from ..utils.errorlog import LuxCoreErrorLog
import concurrent.futures
import multiprocessing
import numpy as np

def convert(scene, context=None, index=0):
    try:
        prefix = "film.imagepipelines.%03d." % index
        definitions = OrderedDict()

        if utils.in_material_shading_mode(context):
            index = _output_switcher(definitions, 0, "ALBEDO")
            _exposure_compensated_tonemapper(definitions, index, scene)
            return utils.create_props(prefix, definitions)

        if utils.using_photongi_debug_mode(context, scene):
            _exposure_compensated_tonemapper(definitions, 0, scene)
            return utils.create_props(prefix, definitions)

        if not utils.is_valid_camera(scene.camera):
            # Can not work without a camera
            _fallback(definitions)
            return utils.create_props(prefix, definitions)

        # Convert definitions in parallel using multiprocessing
        convert_defs(context, scene, definitions, 0)

        return utils.create_props(prefix, definitions)
    except Exception as error:
        import traceback
        traceback.print_exc()
        LuxCoreErrorLog.add_warning('Imagepipeline: %s' % error)
        return pyluxcore.Properties()

def convert_defs(context, scene, definitions, plugin_index, define_radiancescales=True):
    pipeline = scene.camera.data.luxcore.imagepipeline
    using_filesaver = utils.using_filesaver(context, scene)
    # Start index of plugins. Some AOVs prepend their own plugins.
    index = plugin_index

    # Make sure the imagepipeline does nothing when no plugins are enabled
    definitions[str(index) + ".type"] = "NOP"
    index += 1

    # Use multiprocessing for CPU-bound tasks
    with multiprocessing.Pool() as pool:
        results = []

        # Parallel tasks
        if pipeline.tonemapper.enabled:
            results.append(pool.apply_async(convert_tonemapper, (definitions, index, pipeline.tonemapper)))
            index += 1

        if context and scene.luxcore.viewport.get_denoiser(context) == "OPTIX":
            results.append(pool.apply_async(_denoise_effect, (definitions, index, pipeline.denoiser)))
            index += 1

        # Wait for all results to complete
        for result in results:
            result.wait()

    if use_backgroundimage(context, scene):
        # Background image handling (I/O-bound operation, use threading)
        index = _backgroundimage(definitions, index, pipeline.backgroundimage, scene)

    # Handle other image effects using multithreading
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        if pipeline.mist.is_enabled(context):
            futures.append(executor.submit(_mist, definitions, index, pipeline.mist))
            index += 1
        if pipeline.bloom.is_enabled(context):
            futures.append(executor.submit(_bloom, definitions, index, pipeline.bloom))
            index += 1
        if pipeline.coloraberration.is_enabled(context):
            futures.append(executor.submit(_coloraberration, definitions, index, pipeline.coloraberration))
            index += 1
        if pipeline.vignetting.is_enabled(context):
            futures.append(executor.submit(_vignetting, definitions, index, pipeline.vignetting))
            index += 1
        if pipeline.white_balance.is_enabled(context):
            futures.append(executor.submit(_white_balance, definitions, index, pipeline.white_balance))
            index += 1
        if pipeline.camera_response_func.is_enabled(context):
            futures.append(executor.submit(_camera_response_func, definitions, index, pipeline.camera_response_func, scene))
            index += 1
        if pipeline.color_LUT.is_enabled(context):
            futures.append(executor.submit(_color_LUT, definitions, index, pipeline.color_LUT, scene))
            index += 1
        if pipeline.contour_lines.is_enabled(context):
            futures.append(executor.submit(_contour_lines, definitions, index, pipeline.contour_lines))
            index += 1
        if using_filesaver and not pipeline.color_LUT.is_enabled(context):
            futures.append(executor.submit(_gamma, definitions, index))
            index += 1

        # Wait for all futures to complete
        for future in futures:
            future.result()

    if define_radiancescales:
        _lightgroups(definitions, scene)

    return index

def use_backgroundimage(context, scene):
    viewport_in_camera_view = context and context.region_data.view_perspective == "CAMERA"
    final_render = not context
    pipeline = scene.camera.data.luxcore.imagepipeline
    return pipeline.backgroundimage.is_enabled(context) and (final_render or viewport_in_camera_view)

def _fallback(definitions):
    """
    Fallback imagepipeline if no camera is in the scene
    """
    index = 0
    definitions[str(index) + ".type"] = "TONEMAP_LINEAR"
    definitions[str(index) + ".scale"] = 1

def _exposure_compensated_tonemapper(definitions, index, scene):
    definitions[str(index) + ".type"] = "TONEMAP_LINEAR"
    definitions[str(index) + ".scale"] = 1 / pow(2, (scene.view_settings.exposure))
    return index + 1

def convert_tonemapper(definitions, index, tonemapper):
    if tonemapper.type == "TONEMAP_LINEAR" and tonemapper.use_autolinear:
        definitions[str(index) + ".type"] = "TONEMAP_AUTOLINEAR"
        index += 1

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

def _denoise_effect(definitions, index, denoiser):
    definitions[str(index) + ".type"] = "OPTIX_DENOISER"
    definitions[str(index) + ".sharpness"] = 0
    definitions[str(index) + ".minspp"] = denoiser.min_samples
    return index + 1

def _backgroundimage(definitions, index, backgroundimage, scene):
    if backgroundimage.image is None:
        return index

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(ImageExporter.export, backgroundimage.image, backgroundimage.image_user, scene)
            filepath = future.result()
    except OSError as error:
        LuxCoreErrorLog.add_warning(f"Imagepipeline: {error}")
        return index

    definitions[str(index) + ".type"] = "BACKGROUND_IMG"
    definitions[str(index) + ".file"] = filepath
    definitions[str(index) + ".gamma"] = backgroundimage.gamma
    definitions[str(index) + ".storage"] = backgroundimage.storage
    return index + 1

def _gamma(definitions, index):
    definitions[str(index) + ".type"] = "GAMMA_CORRECTION"
    definitions[str(index) + ".value"] = 2.2
    return index + 1

def _color_LUT(definitions, index, color_LUT, scene):
    try:
        library = scene.camera.data.library
        filepath = utils.get_abspath(color_LUT.file, library, must_exist=True, must_be_existing_file=True)
    except OSError as error:
        LuxCoreErrorLog.add_warning(f'Could not find .cube file at path "{color_LUT.file}" ({error})')
        filepath = None

    if filepath:
        gamma_corrected = color_LUT.input_colorspace == "SRGB_GAMMA_CORRECTED"
        if gamma_corrected:
            index = _gamma(definitions, index)

        definitions[str(index) + ".type"] = "COLOR_LUT"
        definitions[str(index) + ".file"] = filepath
        definitions[str(index) + ".strength"] = color_LUT.strength / 100
        return index + 1, gamma_corrected
    else:
        return index, False

def _mist(definitions, index, mist):
    definitions[str(index) + ".type"] = "MIST"
    definitions[str(index) + ".color"] = list(mist.color)
    definitions[str(index) + ".amount"] = mist.amount / 100
    definitions[str(index) + ".startdistance"] = mist.start_distance
    definitions[str(index) + ".enddistance"] = mist.end_distance
    definitions[str(index) + ".excludebackground"] = mist.exclude_background
    return index + 1

def _bloom(definitions, index, bloom):
    definitions[str(index) + ".type"] = "BLOOM"
    definitions[str(index) + ".radius"] = bloom.radius / 100
    definitions[str(index) + ".weight"] = bloom.weight / 100
    return index + 1

def _coloraberration(definitions, index, coloraberration):
    definitions[str(index) + ".type"] = "COLOR_ABERRATION"
    amount_x = coloraberration.amount / 100
    amount_y = coloraberration.amount_y / 100
    if coloraberration.uniform:
        definitions[str(index) + ".amount"] = amount_x
    else:
        definitions[str(index) + ".amount"] = [amount_x, amount_y]
    return index + 1

def _vignetting(definitions, index, vignetting):
    definitions[str(index) + ".type"] = "VIGNETTING"
    definitions[str(index) + ".scale"] = vignetting.scale / 100
    return index + 1

def _white_balance(definitions, index, white_balance):
    definitions[str(index) + ".type"] = "WHITE_BALANCE"
    definitions[str(index) + ".temperature"] = white_balance.temperature
    definitions[str(index) + ".reverse"] = white_balance.reverse
    definitions[str(index) + ".normalize"] = True
    return index + 1

def _camera_response_func(definitions, index, camera_response_func, scene):
    if camera_response_func.type == "PRESET":
        name = camera_response_func.preset
    elif camera_response_func.type == "FILE":
        try:
            library = scene.camera.data.library
            name = utils.get_abspath(camera_response_func.file, library, must_exist=True, must_be_existing_file=True)
        except OSError as error:
            LuxCoreErrorLog.add_warning(f'Could not find .crf file at path "{camera_response_func.file}" ({error})')
            name = None
    else:
        raise NotImplementedError("Unknown crf type: " + camera_response_func.type)

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

def _lightgroups(definitions, scene):
    lightgroups = scene.luxcore.lightgroups
    _lightgroup(definitions, lightgroups.default, 0)

    for i, group in enumerate(lightgroups.custom):
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
