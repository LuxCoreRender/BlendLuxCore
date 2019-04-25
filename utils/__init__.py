import bpy
import mathutils
import math
import re
import os
import hashlib
from ..bin import pyluxcore

NON_DEFORMING_MODIFIERS = {"COLLISION", "PARTICLE_INSTANCE", "PARTICLE_SYSTEM", "SMOKE"}


class ExportedObject(object):
    def __init__(self, mesh_definitions, luxcore_name):
        """
        :param luxcore_name: The true base name of this object (without material index suffix). Passed
                             separately because the names in mesh_definitions are incorrect for shared meshes
        """

        # Note that luxcore_names is a list of names (because an object in Blender can have multiple materials,
        # while in LuxCore it can have only one material, so we have to split it into multiple LuxCore objects)
        self.luxcore_names = []
        for _, material_index in mesh_definitions:
            self.luxcore_names.append(luxcore_name + "%03d" % material_index)
        # list of lists of the form [lux_obj_name, material_index]
        self.mesh_definitions = mesh_definitions


class ExportedLight(object):
    def __init__(self, luxcore_name):
        # this is a list to make it compatible with ExportedObject
        self.luxcore_names = [luxcore_name]


def sanitize_luxcore_name(string):
    """
    Do NOT use this function to create a luxcore name for an object/material/etc.!
    Use the function get_luxcore_name() instead.
    This is just a regex that removes non-allowed characters.
    """
    return re.sub("[^_0-9a-zA-Z]+", "__", string)


def make_key(datablock):
    # We use the memory address as key, e.g. to track materials or objects even when they are
    # renamed during viewport render.
    # Note that the memory address changes on undo/redo, but in this case the viewport render
    # is stopped and re-started anyway, so it should not be a problem.
    return str(datablock.as_pointer())


def make_key_from_name(datablock):
    """ Old make_key method, not sure if we need it anymore """
    key = datablock.name
    if hasattr(datablock, "type"):
        key += datablock.type
    if hasattr(datablock, "data") and hasattr(datablock.data, "type"):
        key += datablock.data.type
    if datablock.library:
        key += datablock.library.name
    return key


def get_pretty_name(datablock):
    name = datablock.name

    if hasattr(datablock, "type"):
        name = datablock.type.title() + "_" + name

    return name


def get_luxcore_name(datablock, is_viewport_render=True):
    """
    This is the function you should use to get a unique luxcore name
    for a datablock (object, lamp, material etc.).
    If is_viewport_render is True, the name is persistent even if
    the user renames the datablock.

    Note that we can't use pretty names in viewport render.
    If we would do that, renaming a datablock during the render
    would change all references to it.
    """
    key = make_key(datablock)

    if not is_viewport_render:
        # Final render - we can use pretty names
        key = sanitize_luxcore_name(get_pretty_name(datablock)) + "_" + key

    return key


def obj_from_key(key, objects):
    for obj in objects:
        if key == make_key(obj):
            return obj
    return None


def make_object_id(name):
    # We do this similar to Cycles: hash the object's name to get a "stable" object ID
    digest = hashlib.md5(name.encode("utf-8")).digest()
    as_int = int.from_bytes(digest, byteorder="little")
    # Truncate to 4 bytes because LuxCore uses unsigned int for the object ID.
    # Make sure it's not exactly 0xffffffff because that's LuxCore's Null index for object IDs.
    return min(as_int & 0xffffffff, 0xffffffff - 1)


def create_props(prefix, definitions):
    """
    :param prefix: string, will be prepended to each key part of the definitions.
                   Example: "scene.camera." (note the trailing dot)
    :param definitions: dictionary of definition pairs. Example: {"fieldofview", 45}
    :return: pyluxcore.Properties() object, initialized with the given definitions.
    """
    props = pyluxcore.Properties()

    for k, v in definitions.items():
        props.Set(pyluxcore.Property(prefix + k, v))

    return props


def get_worldscale(scene, as_scalematrix=True):
    unit_settings = scene.unit_settings

    if unit_settings.system in {"METRIC", "IMPERIAL"}:
        # The units used in modelling are for display only. behind
        # the scenes everything is in meters
        ws = unit_settings.scale_length
    else:
        ws = 1

    if as_scalematrix:
        return mathutils.Matrix.Scale(ws, 4)
    else:
        return ws


def get_scaled_to_world(matrix, scene):
    matrix = matrix.copy()
    sm = get_worldscale(scene)
    matrix *= sm
    ws = get_worldscale(scene, as_scalematrix=False)
    matrix[0][3] *= ws
    matrix[1][3] *= ws
    matrix[2][3] *= ws
    return matrix


def matrix_to_list(matrix, scene=None, apply_worldscale=False, invert=False):
    """
    Flatten a 4x4 matrix into a list
    Returns list[16]
    You only have to pass a valid scene if apply_worldscale is True
    """

    if apply_worldscale:
        matrix = get_scaled_to_world(matrix, scene)

    if invert:
        matrix = matrix.copy()
        matrix.invert_safe()

    l = [matrix[0][0], matrix[1][0], matrix[2][0], matrix[3][0],
         matrix[0][1], matrix[1][1], matrix[2][1], matrix[3][1],
         matrix[0][2], matrix[1][2], matrix[2][2], matrix[3][2],
         matrix[0][3], matrix[1][3], matrix[2][3], matrix[3][3]]

    if matrix.determinant() == 0:
        # The matrix is non-invertible. This can happen if e.g. the scale on one axis is 0.
        # Prevent a RuntimeError from LuxCore by adding a small random epsilon.
        # TODO maybe look for a better way to handle this
        from random import random
        return [float(i) + (1e-5 + random() * 1e-5) for i in l]
    else:
        return [float(i) for i in l]


def calc_filmsize_raw(scene, context=None):
    if context:
        # Viewport render
        width = context.region.width
        height = context.region.height
    else:
        # Final render
        scale = scene.render.resolution_percentage / 100
        width = int(scene.render.resolution_x * scale)
        height = int(scene.render.resolution_y * scale)

    return width, height


def calc_filmsize(scene, context=None):
    render = scene.render
    border_min_x, border_max_x, border_min_y, border_max_y = calc_blender_border(scene, context)
    width_raw, height_raw = calc_filmsize_raw(scene, context)
    
    if context:
        # Viewport render        
        width = width_raw
        height = height_raw
        if context.region_data.view_perspective in ("ORTHO", "PERSP"):            
            width = int(width_raw * border_max_x) - int(width_raw * border_min_x)
            height = int(height_raw * border_max_y) - int(height_raw * border_min_y)
        else:
            # Camera viewport
            zoom = 0.25 * ((math.sqrt(2) + context.region_data.view_camera_zoom / 50) ** 2)
            aspectratio, aspect_x, aspect_y = calc_aspect(render.resolution_x * render.pixel_aspect_x,
                                                          render.resolution_y * render.pixel_aspect_y,
                                                          scene.camera.data.sensor_fit)

            if render.use_border:
                base = zoom
                if scene.camera.data.sensor_fit == "AUTO":
                    base *= max(width, height)
                elif scene.camera.data.sensor_fit == "HORIZONTAL":
                    base *= width
                elif scene.camera.data.sensor_fit == "VERTICAL":
                    base *= height

                width = int(base * aspect_x * border_max_x) - int(base * aspect_x * border_min_x)
                height = int(base * aspect_y * border_max_y) - int(base * aspect_y * border_min_y)

        pixel_size = int(scene.luxcore.viewport.pixel_size)
        width //= pixel_size
        height //= pixel_size
    else:
        # Final render
        width = int(width_raw * border_max_x) - int(width_raw * border_min_x)
        height = int(height_raw * border_max_y) - int(height_raw * border_min_y)

    # Make sure width and height are never zero
    # (can e.g. happen if you have a small border in camera viewport and zoom out a lot)
    width = max(2, width)
    height = max(2, height)

    return width, height


def calc_blender_border(scene, context=None):
    render = scene.render

    if context and context.region_data.view_perspective in ("ORTHO", "PERSP"):
        # Viewport camera
        border_max_x = context.space_data.render_border_max_x
        border_max_y = context.space_data.render_border_max_y
        border_min_x = context.space_data.render_border_min_x
        border_min_y = context.space_data.render_border_min_y
    else:
        # Final camera
        border_max_x = render.border_max_x
        border_max_y = render.border_max_y
        border_min_x = render.border_min_x
        border_min_y = render.border_min_y

    if context and context.region_data.view_perspective in ("ORTHO", "PERSP"):
        use_border = context.space_data.use_render_border
    else:
        use_border = render.use_border

    if use_border:
        blender_border = [border_min_x, border_max_x, border_min_y, border_max_y]
        # Round all values to avoid running into problems later
        # when a value is for example 0.699999988079071
        blender_border = [round(value, 6) for value in blender_border]
    else:
        blender_border = [0, 1, 0, 1]

    return blender_border


def calc_screenwindow(zoom, shift_x, shift_y, scene, context=None):
    # shift is in range -2..2
    # offset is in range -4..4
    render = scene.render

    width_raw, height_raw = calc_filmsize_raw(scene, context)
    border_min_x, border_max_x, border_min_y, border_max_y = calc_blender_border(scene, context)
    world_scale = get_worldscale(scene, False)

    # Following: Black Magic
    scale = 1
    offset_x = 0
    offset_y = 0
    
    if context:
        # Viewport rendering
        if context.region_data.view_perspective == "CAMERA":
            offset_x, offset_y = context.region_data.view_camera_offset
            # Camera view            
            if render.use_border:
                offset_x = 0
                offset_y = 0
                zoom = 1
                aspectratio, xaspect, yaspect = calc_aspect(render.resolution_x * render.pixel_aspect_x,
                                                            render.resolution_y * render.pixel_aspect_y,
                                                            scene.camera.data.sensor_fit)
                    
                if scene.camera and scene.camera.data.type == "ORTHO":
                    zoom = 0.5 * scene.camera.data.ortho_scale * world_scale
                    scale = zoom
            else:
                # No border
                aspectratio, xaspect, yaspect = calc_aspect(width_raw, height_raw, scene.camera.data.sensor_fit)
        else:
            # Normal viewport
            aspectratio, xaspect, yaspect = calc_aspect(width_raw, height_raw)
    else:
        # Final rendering
        aspectratio, xaspect, yaspect = calc_aspect(render.resolution_x * render.pixel_aspect_x,
                                                    render.resolution_y * render.pixel_aspect_y,
                                                    scene.camera.data.sensor_fit)

    dx = scale * 2 * (shift_x + 2 * xaspect * offset_x)
    dy = scale * 2 * (shift_y + 2 * yaspect * offset_y)

    screenwindow = [
        -xaspect*zoom + dx,
         xaspect*zoom + dx,
        -yaspect*zoom + dy,
         yaspect*zoom + dy
    ]
    
    screenwindow = [
        screenwindow[0] * (1 - border_min_x) + screenwindow[1] * border_min_x,
        screenwindow[0] * (1 - border_max_x) + screenwindow[1] * border_max_x,
        screenwindow[2] * (1 - border_min_y) + screenwindow[3] * border_min_y,
        screenwindow[2] * (1 - border_max_y) + screenwindow[3] * border_max_y
    ]
    
    return screenwindow


def calc_aspect(width, height, fit="AUTO"):
    horizontal_fit = False
    if fit == "AUTO":
        horizontal_fit = (width > height)
    elif fit == "HORIZONTAL":
        horizontal_fit = True
    
    if horizontal_fit:
        aspect = height / width
        xaspect = 1
        yaspect = aspect
    else:
        aspect = width / height
        xaspect = aspect
        yaspect = 1
    
    return aspect, xaspect, yaspect


def find_active_uv(uv_textures):
    for uv in uv_textures:
        if uv.active_render:
            return uv
    return None


def find_active_vertex_color_layer(vertex_colors):
    for layer in vertex_colors:
        if layer.active_render:
            return layer
    return None


def is_obj_visible(obj, scene, context=None, is_dupli=False):
    """
    Find out if an object is visible.
    Note: if the object is an emitter, check emitter visibility with is_duplicator_visible() below.
    """
    if is_dupli:
        return True

    # Mimic Blender behaviour: if object is duplicated via a parent, it should be invisible
    if obj.parent and obj.parent.dupli_type != "NONE":
        return False

    # Check if object is used as camera clipping plane
    if is_valid_camera(scene.camera) and obj == scene.camera.data.luxcore.clipping_plane:
        return False

    render_layer = get_current_render_layer(scene)
    if render_layer:
        # We need the list of excluded layers in the settings of this render layer
        exclude_layers = render_layer.layers_exclude
    else:
        # We don't account for render layer visiblity in viewport/preview render
        # so we create a mock list here
        exclude_layers = [False] * 20

    on_visible_layer = False
    for lv in [ol and sl and not el for ol, sl, el in zip(obj.layers, scene.layers, exclude_layers)]:
        on_visible_layer |= lv

    hidden_in_outliner = obj.hide if context else obj.hide_render
    return on_visible_layer and not hidden_in_outliner


def is_obj_visible_to_cam(obj, scene, context=None):
    visible_to_cam = obj.luxcore.visible_to_camera
    render_layer = get_current_render_layer(scene)

    if render_layer:
        on_visible_layer = False
        for lv in [ol and sl for ol, sl in zip(obj.layers, render_layer.layers)]:
            on_visible_layer |= lv

        return visible_to_cam and on_visible_layer
    else:
        # We don't account for render layer visiblity in viewport/preview render
        return visible_to_cam


def is_duplicator_visible(obj):
    """ Find out if a particle/hair emitter or duplicator is visible """
    assert obj.is_duplicator

    # obj.is_duplicator is also true if it has particle/hair systems - they allow to show the duplicator
    for psys in obj.particle_systems:
        if psys.settings.use_render_emitter:
            return True

    # Dupliframes duplicate the original object, so it must be visible
    if obj.dupli_type == "FRAMES":
        return True

    # Duplicators (Dupliverts/faces) are always hidden
    return False


def get_theme(context):
    current_theme_name = context.user_preferences.themes.items()[0][0]
    return context.user_preferences.themes[current_theme_name]


def get_abspath(path, library=None, must_exist=False, must_be_existing_file=False, must_be_existing_dir=False):
    """ library: The library this path is from. """
    assert not (must_be_existing_file and must_be_existing_dir)

    abspath = bpy.path.abspath(path, library=library)

    if must_be_existing_file and not os.path.isfile(abspath):
        raise OSError('Not an existing file: "%s"' % abspath)

    if must_be_existing_dir and not os.path.isdir(abspath):
        raise OSError('Not an existing directory: "%s"' % abspath)

    if must_exist and not os.path.exists(abspath):
        raise OSError('Path does not exist: "%s"' % abspath)

    return abspath


def absorption_at_depth_scaled(abs_col, depth, scale=1):
    abs_col = list(abs_col)
    assert len(abs_col) == 3

    scaled = [0, 0, 0]
    for i in range(len(abs_col)):
        v = float(abs_col[i])
        scaled[i] = (-math.log(max([v, 1e-30])) / depth) * scale * (v == 1.0 and -1 or 1)

    return scaled


def all_elems_equal(_list):
    # https://stackoverflow.com/a/10285205
    # The list must not be empty!
    first = _list[0]
    return all(x == first for x in _list)


def use_obj_motion_blur(obj, scene):
    """ Check if this particular object will be exported with motion blur """
    cam = scene.camera

    if cam is None:
        return False

    motion_blur = cam.data.luxcore.motion_blur
    object_blur = motion_blur.enable and motion_blur.object_blur

    return object_blur and obj.luxcore.enable_motion_blur


def can_share_mesh(obj):
    modified = any([mod.type not in NON_DEFORMING_MODIFIERS for mod in obj.modifiers])
    return not modified and obj.data and obj.data.users > 1


def use_instancing(obj, scene, context):
    if context:
        # Always instance in viewport so we can move the object/light around
        return True

    if use_obj_motion_blur(obj, scene):
        # When using object motion blur, we export all objects as instances
        return True

    # Alt+D copies without deforming modifiers
    if can_share_mesh(obj):
        return True

    return False


def find_smoke_domain_modifier(obj):
    for mod in obj.modifiers:
        if mod.type == "SMOKE" and mod.smoke_type == "DOMAIN":
            return mod
    return None


def get_name_with_lib(datablock):
    """
    Format the name for display similar to Blender,
    with an "L" as prefix if from a library
    """
    text = datablock.name
    if datablock.library:
        # text += ' (Lib: "%s")' % datablock.library.name
        text = "L " + text
    return text


def clamp(value, _min=0, _max=1):
    return max(_min, min(_max, value))


def use_filesaver(context, scene):
    return context is None and scene.luxcore.config.use_filesaver


def get_current_render_layer(scene):
    """ This is the layer that is currently being exported, not the active layer in the UI """
    active_layer_index = scene.luxcore.active_layer_index

    # If active layer index is -1 we are trying to access it
    # in an incorrect situation, e.g. viewport render
    if active_layer_index == -1:
        return None

    return scene.render.layers[active_layer_index]


def get_halt_conditions(scene):
    render_layer = get_current_render_layer(scene)

    if render_layer and render_layer.luxcore.halt.enable:
        # Global halt conditions are overridden by this render layer
        return render_layer.luxcore.halt
    else:
        # Use global halt conditions
        return scene.luxcore.halt


def use_two_tiled_passes(scene):
    # When combining the BCD denoiser with tilepath in singlepass mode, we have to render
    # two passes (twice as many samples) because the first pass is needed as denoiser
    # warmup, and only during the second pass can the denoiser collect sample information.
    config = scene.luxcore.config
    denoiser = scene.luxcore.denoiser
    using_tilepath = config.engine == "PATH" and config.use_tiles
    return denoiser.enabled and denoiser.type == "BCD" and using_tilepath and not config.tile.multipass_enable


def pluralize(format_str, amount):
    formatted = format_str % amount
    if amount != 1:
        formatted += "s"
    return formatted


def is_opencl_build():
    return not pyluxcore.GetPlatformDesc().Get("compile.LUXRAYS_DISABLE_OPENCL").GetBool()


def image_sequence_resolve_all(image):
    """
    From https://blender.stackexchange.com/a/21093/29401
    Returns a list of tuples: (index, filepath)
    index is the frame number, parsed from the filepath
    """
    filepath = get_abspath(image.filepath, image.library)
    basedir, filename = os.path.split(filepath)
    filename_noext, ext = os.path.splitext(filename)

    from string import digits
    if isinstance(filepath, bytes):
        digits = digits.encode()
    filename_nodigits = filename_noext.rstrip(digits)

    if len(filename_nodigits) == len(filename_noext):
        # Input isn't from a sequence
        return []

    indexed_filepaths = []
    for f in os.scandir(basedir):
        index_str = f.name[len(filename_nodigits):-len(ext) if ext else -1]

        if (f.is_file()
                and f.name.startswith(filename_nodigits)
                and f.name.endswith(ext)
                and index_str.isdigit()):
            elem = (int(index_str), f.path)
            indexed_filepaths.append(elem)

    return sorted(indexed_filepaths, key=lambda elem: elem[0])


def is_valid_camera(obj):
    return obj and hasattr(obj, "type") and obj.type == "CAMERA"


def get_blendfile_name():
    basename = bpy.path.basename(bpy.data.filepath)
    return os.path.splitext(basename)[0]  # remove ".blend"
