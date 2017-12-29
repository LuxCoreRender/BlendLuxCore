import mathutils
import math
import re
from ..bin import pyluxcore


class ExportedObject(object):
    def __init__(self, mesh_definitions):
        # Note that luxcore_names is a list of names (because an object in Blender can have multiple materials,
        # while in LuxCore it can have only one material, so we have to split it into multiple LuxCore objects)
        self.luxcore_names = [lux_obj_name for lux_obj_name, material_index in mesh_definitions]
        # list of lists of the form [lux_obj_name, material_index]
        self.mesh_definitions = mesh_definitions


class ExportedLight(object):
    def __init__(self, luxcore_name):
        # this is a list to make it compatible with ExportedObject
        self.luxcore_names = [luxcore_name]


def to_luxcore_name(string):
    return re.sub("[^_0-9a-zA-Z]+", "__", string)


def make_key(datablock):
    key = datablock.name
    if hasattr(datablock, "type"):
        key += datablock.type
    if hasattr(datablock, "data") and hasattr(datablock.data, "type"):
        key += datablock.data.type
    if datablock.library:
        key += datablock.library.name
    return key


def get_unique_luxcore_name(datablock):
    return to_luxcore_name(make_key(datablock))


def obj_from_key(key, objects):
    for obj in objects:
        if key == make_key(obj):
            return obj
    return None


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

    if unit_settings.system in ["METRIC", "IMPERIAL"]:
        # The units used in modelling are for display only. behind
        # the scenes everything is in meters
        ws = unit_settings.scale_length
    else:
        ws = 1

    if as_scalematrix:
        return mathutils.Matrix.Scale(ws, 4)
    else:
        return ws


def matrix_to_list(matrix, scene=None, apply_worldscale=False, invert=False):
    """
    Flatten a 4x4 matrix into a list
    Returns list[16]
    You only have to pass a valid scene if apply_worldscale is True
    """

    if apply_worldscale:
        assert scene is not None
        matrix = matrix.copy()
        sm = get_worldscale(scene)
        matrix *= sm
        ws = get_worldscale(scene, as_scalematrix=False)
        matrix[0][3] *= ws
        matrix[1][3] *= ws
        matrix[2][3] *= ws

    if invert:
        matrix = matrix.inverted()

    l = [matrix[0][0], matrix[1][0], matrix[2][0], matrix[3][0],
         matrix[0][1], matrix[1][1], matrix[2][1], matrix[3][1],
         matrix[0][2], matrix[1][2], matrix[2][2], matrix[3][2],
         matrix[0][3], matrix[1][3], matrix[2][3], matrix[3][3]]

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
    border_min_x, border_max_x, border_min_y, border_max_y = calc_blender_border(scene, context)
    width_raw, height_raw = calc_filmsize_raw(scene, context)
    
    if context:
        # Viewport render        
        width = width_raw
        height = height_raw
        if context.region_data.view_perspective in ("ORTHO", "PERSP"):
            width = round(width_raw * (border_max_x - border_min_x))
            height = round(height_raw * (border_max_y - border_min_y))
        else:
            # Camera viewport
            if scene.render.use_border:
                aspect_x, aspect_y = calc_aspect(scene.render.resolution_x, scene.render.resolution_y)
                zoom = 0.25 * ((math.sqrt(2) + context.region_data.view_camera_zoom / 50) ** 2)

                base = max(width_raw, height_raw)
                width = round(zoom * base * aspect_x * (border_max_x - border_min_x))
                height = round(zoom * base * aspect_y * (border_max_y - border_min_y))
    else:
        width = round(width_raw * (border_max_x - border_min_x))
        height = round(height_raw * (border_max_y - border_min_y))

    return width, height


def calc_blender_border(scene, context=None):
    if context and context.region_data.view_perspective in ("ORTHO", "PERSP"):
        # Viewport camera
        border_max_x = context.space_data.render_border_max_x
        border_max_y = context.space_data.render_border_max_y
        border_min_x = context.space_data.render_border_min_x
        border_min_y = context.space_data.render_border_min_y
    else:
        # Final camera
        border_max_x = scene.render.border_max_x
        border_max_y = scene.render.border_max_y
        border_min_x = scene.render.border_min_x
        border_min_y = scene.render.border_min_y

    if context and context.region_data.view_perspective in ("ORTHO", "PERSP"):
        use_border = context.space_data.use_render_border
    else:
        use_border = scene.render.use_border

    if use_border:
        blender_border = [border_min_x, border_max_x, border_min_y, border_max_y]
    else:
        blender_border = [0, 1, 0, 1]

    return blender_border


def calc_screenwindow(zoom, shift_x, shift_y, offset_x, offset_y, scene, context=None):
    # offset and shift are in range -1..1 ( I think)

    width_raw, height_raw = calc_filmsize_raw(scene, context)
    border_min_x, border_max_x, border_min_y, border_max_y = calc_blender_border(scene, context)

    # Following: Black Magic
    
    if context:
        # Viewport rendering            
        if context.region_data.view_perspective == "CAMERA" and scene.render.use_border:
            # Camera view
            xaspect, yaspect = calc_aspect(scene.render.resolution_x, scene.render.resolution_y)
                
            screenwindow = [
                (2*shift_x) - xaspect,
                (2*shift_x) + xaspect,
                (2*shift_y) - yaspect,
                (2*shift_y) + yaspect
            ]            
            
            screenwindow = [
                screenwindow[0] * (1 - border_min_x) + screenwindow[1] * border_min_x,
                screenwindow[0] * (1 - border_max_x) + screenwindow[1] * border_max_x,
                screenwindow[2] * (1 - border_min_y) + screenwindow[3] * border_min_y,
                screenwindow[2] * (1 - border_max_y) + screenwindow[3] * border_max_y
            ]            
        else:
            # Normal viewport            
            xaspect, yaspect = calc_aspect(width_raw, height_raw)

            screenwindow = [
                (2*shift_x) - xaspect*zoom,
                (2*shift_x) + xaspect*zoom,
                (2*shift_y) - yaspect*zoom,
                (2*shift_y) + yaspect*zoom
            ]

            screenwindow = [
                screenwindow[0] * (1 - border_min_x) + screenwindow[1] * border_min_x + offset_x,
                screenwindow[0] * (1 - border_max_x) + screenwindow[1] * border_max_x + offset_x,
                screenwindow[2] * (1 - border_min_y) + screenwindow[3] * border_min_y + offset_y,
                screenwindow[2] * (1 - border_max_y) + screenwindow[3] * border_max_y + offset_y
            ]
    else:
        #Final rendering
        xaspect, yaspect = calc_aspect(scene.render.resolution_x, scene.render.resolution_y)
        screenwindow = [
            ((2 * shift_x) - xaspect),
            ((2 * shift_x) + xaspect),
            ((2 * shift_y) - yaspect),
            ((2 * shift_y) + yaspect)
        ]

        screenwindow = [
            screenwindow[0] * (1 - border_min_x) + screenwindow[1] * border_min_x + offset_x,
            screenwindow[0] * (1 - border_max_x) + screenwindow[1] * border_max_x + offset_x,
            screenwindow[2] * (1 - border_min_y) + screenwindow[3] * border_min_y + offset_y,
            screenwindow[2] * (1 - border_max_y) + screenwindow[3] * border_max_y + offset_y
        ]
    return screenwindow


def calc_aspect(width, height):
    if width > height:
        xaspect = 1
        yaspect = height / width
    else:
        xaspect = width / height
        yaspect = 1
    return xaspect, yaspect


def find_active_uv(uv_textures):
    for uv in uv_textures:
        if uv.active_render:
            return uv
    return None


def is_obj_visible(obj, scene, context=None, is_dupli=False):
    hidden = obj.hide if context else obj.hide_render

    renderlayer = scene.render.layers.active.layers
    visible = False
    for lv in [ol and sl and rl for ol, sl, rl in zip(obj.layers, scene.layers, renderlayer)]:
        visible |= lv
    return (visible or is_dupli) and not hidden

def get_theme(context):
    current_theme_name = context.user_preferences.themes.items()[0][0]
    return context.user_preferences.themes[current_theme_name]
