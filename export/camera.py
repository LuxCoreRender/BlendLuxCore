import math
from mathutils import Vector, Matrix
from ..bin import pyluxcore
from .. import utils


def needs_update():
    # TODO (store info in cache or so? and rely on cam_obj.is_updated for stuff like special parameters?)
    return True


def convert(scene, context=None):
    print("converting camera")

    if context:
        # Viewport render
        view_cam_type = context.region_data.view_perspective

        width = context.region.width
        height = context.region.height

        if view_cam_type == 'ORTHO':
            type = "orthographic"
        elif view_cam_type == 'PERSP':
            type = "perspective"
            cam_matrix = Matrix(context.region_data.view_matrix).inverted()
            fieldofview = math.degrees(2 * math.atan(16 / context.space_data.lens))

            zoom = 2
            dx = 0
            dy = 0
            screenwindow = calc_screenwindow(dx, dy, width, height, zoom)
        elif view_cam_type == 'CAMERA':
            camera = scene.camera
            cam_matrix = camera.matrix_world

            if camera.data.type == 'ORTHO':
                type = "orthographic"
            elif camera.data.type == 'PANO':
                type = "environment"
            else:
                type = "perspective"
                fieldofview = math.degrees(camera.data.angle)
    else:
        # Final render
        pass

    # Lookat
    lookat_target = list(cam_matrix * Vector((0, 0, -1)))
    lookat_orig = list(cam_matrix.to_translation())
    up_vector = list(cam_matrix.to_3x3() * Vector((0, 1, 0)))

    prefix = "scene.camera."
    definitions = {
        "type": type,
        "lookat.target": lookat_target,
        "lookat.orig": lookat_orig,
        "up": up_vector,
        #"lensradius": lensradius,
        #"focaldistance": focaldistance,
        #"screenwindow": screenwindow,
        #"cliphither": clip_hither,
        #"clipyon": clip_yon,
        #"shutteropen": shutter_open,
        #"shutterclose": shutter_close,
    }

    if type == "perspective":
        definitions["fieldofview"] = fieldofview

    if type != "environment":
        #definitions["autofocus.enable"] = use_autofocus

        use_clippingplane = False  # TODO
        if use_clippingplane:
            definitions.update({
                "clippingplane.enable": use_clippingplane,
                "clippingplane.center": clippingplane_center,
                "clippingplane.normal": clippingplane_normal,
            })

    # TODO: motion blur (only for final camera)

    return utils.create_props(prefix, definitions)


def calc_screenwindow(dx, dy, width, height, zoom):
    xaspect, yaspect = calc_aspect(width, height)
    left = -xaspect * zoom
    right = xaspect * zoom
    bottom = -yaspect * zoom
    top = yaspect * zoom

    return [left + dx, right + dx, bottom + dy, top + dy]

def calc_aspect(width, height):
    if width > height:
        xaspect = 1
        yaspect = height / width
    else:
        xaspect = width / height
        yaspect = 1
    return xaspect, yaspect