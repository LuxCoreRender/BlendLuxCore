import math
from mathutils import Vector, Matrix
from ..bin import pyluxcore
from .. import utils


def needs_update():
    # TODO (store info in cache or so? and rely on cam_obj.is_updated for stuff like special parameters?)
    return True


def convert(scene, context=None):
    if context:
        # Viewport render
        view_cam_type = context.region_data.view_perspective

        if view_cam_type in ('ORTHO', 'PERSP'):
            cam_matrix = Matrix(context.region_data.view_matrix).inverted()
            lookat_orig, lookat_target, up_vector = _calc_lookat(cam_matrix)

            if view_cam_type == 'ORTHO':
                type = "orthographic"
                zoom = context.space_data.region_3d.view_distance

                # Move the camera origin away from the viewport center to avoid clipping
                origin = Vector(lookat_orig)
                target = Vector(lookat_target)
                origin += (origin - target) * 50
                lookat_orig = list(origin)
            else:
                # view_cam_type == 'PERSP'
                type = "perspective"
                zoom = 2
                # Magic stuff, found in Cycles export code
                # TODO: non-standard sensor (is that where the 0.5 * 32 came from?)
                fieldofview = math.degrees(2 * math.atan(16 / context.space_data.lens))

            screenwindow = utils.calc_screenwindow(zoom, 0, 0, 0, 0, scene, context)
        else:
            # view_cam_type == 'CAMERA'
            camera = scene.camera
            cam_matrix = camera.matrix_world
            lookat_orig, lookat_target, up_vector = _calc_lookat(cam_matrix)
            # Magic zoom formula for camera viewport zoom from Cycles export code
            zoom = 2 / ((math.sqrt(2) + context.region_data.view_camera_zoom / 50) ** 2) * 2

            if camera.data.type == 'ORTHO':
                type = "orthographic"
                zoom *= camera.data.ortho_scale / 2
            elif camera.data.type == 'PANO':
                type = "environment"
            else:
                # camera.data.type == 'PERSP'
                type = "perspective"
                fieldofview = math.degrees(camera.data.angle)

            xaspect, yaspect = utils.calc_aspect(context.region.width, context.region.height)
            view_camera_offset = list(context.region_data.view_camera_offset)
            offset_x = 2 * (camera.data.shift_x + view_camera_offset[0] * xaspect * 2)
            offset_y = 2 * (camera.data.shift_y + view_camera_offset[1] * yaspect * 2)
            screenwindow = utils.calc_screenwindow(zoom, 0, 0, offset_x, offset_y, scene, context)
    else:
        # Final render
        pass

    # Lookat


    prefix = "scene.camera."
    definitions = {
        "type": type,
        "lookat.orig": lookat_orig,
        "lookat.target": lookat_target,
        "up": up_vector,
        #"lensradius": lensradius,
        #"focaldistance": focaldistance,
        "screenwindow": screenwindow,
        #"cliphither": clip_hither,
        #"clipyon": clip_yon,
        #"shutteropen": shutter_open,
        #"shutterclose": shutter_close,
    }

    if type == "perspective":
        definitions["fieldofview"] = fieldofview

    if type != "environment":
        #definitions["autofocus.enable"] = use_autofocus  # TODO

        use_clippingplane = False  # TODO
        if use_clippingplane:
            definitions.update({
                "clippingplane.enable": use_clippingplane,
                "clippingplane.center": clippingplane_center,
                "clippingplane.normal": clippingplane_normal,
            })

    # TODO: motion blur (only for final camera)

    return utils.create_props(prefix, definitions)


def _calc_lookat(cam_matrix):
    lookat_orig = list(cam_matrix.to_translation())
    lookat_target = list(cam_matrix * Vector((0, 0, -1)))
    up_vector = list(cam_matrix.to_3x3() * Vector((0, 1, 0)))
    return lookat_orig, lookat_target, up_vector
