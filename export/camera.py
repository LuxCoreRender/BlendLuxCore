import math
from mathutils import Vector, Matrix
from ..bin import pyluxcore
from .. import utils


def needs_update():
    # TODO (store info in cache or so? and rely on cam_obj.is_updated for stuff like special parameters?)
    return True


def convert(scene, context=None):
    try:
        prefix = "scene.camera."
        definitions = {}

        if context:
            # Viewport render
            view_cam_type = context.region_data.view_perspective

            if view_cam_type == "ORTHO":
                _view_ortho(scene, context, definitions)
            elif view_cam_type == "PERSP":
                _view_persp(scene, context, definitions)
            elif view_cam_type == "CAMERA":
                _view_camera(scene, context, definitions)
            else:
                raise NotImplementedError("Unknown context.region_data.view_perspective")
        else:
            # Final render
            _final(scene, definitions)

        _clipping(scene, definitions)
        _clipping_plane(scene, definitions)

        return utils.create_props(prefix, definitions)
    except Exception as error:
        msg = 'Camera: %s' % error
        scene.luxcore.errorlog.add_warning(msg)
        return pyluxcore.Properties()


def _view_ortho(scene, context, definitions):
    cam_matrix = Matrix(context.region_data.view_matrix).inverted()
    lookat_orig, lookat_target, up_vector = _calc_lookat(cam_matrix)

    definitions["type"] = "orthographic"
    zoom = 0.915 * context.space_data.region_3d.view_distance

    # Move the camera origin away from the viewport center to avoid clipping
    origin = Vector(lookat_orig)
    target = Vector(lookat_target)
    origin += (origin - target) * 50
    definitions["lookat.orig"] = list(origin)
    definitions["lookat.target"] = lookat_target
    definitions["up"] = up_vector

    definitions["screenwindow"] = utils.calc_screenwindow(zoom, 0, 0, 0, 0, scene, context)


def _view_persp(scene, context, definitions):
    cam_matrix = Matrix(context.region_data.view_matrix).inverted()
    lookat_orig, lookat_target, up_vector = _calc_lookat(cam_matrix)
    definitions["lookat.orig"] = lookat_orig
    definitions["lookat.target"] = lookat_target
    definitions["up"] = up_vector

    definitions["type"] = "perspective"
    zoom = 2
    # Magic stuff, found in Cycles export code
    # TODO: non-standard sensor (is that where the 0.5 * 32 came from?)
    definitions["fieldofview"] = math.degrees(2 * math.atan(16 / context.space_data.lens))

    definitions["screenwindow"] = utils.calc_screenwindow(zoom, 0, 0, 0, 0, scene, context)


def _view_camera(scene, context, definitions):
    camera = scene.camera
    lookat_orig, lookat_target, up_vector = _calc_lookat(camera.matrix_world)
    definitions["lookat.orig"] = lookat_orig
    definitions["lookat.target"] = lookat_target
    definitions["up"] = up_vector

    # Magic zoom formula for camera viewport zoom from Cycles export code
    zoom = 4 / ((math.sqrt(2) + context.region_data.view_camera_zoom / 50) ** 2)

    if camera.data.type == "ORTHO":
        definitions["type"] = "orthographic"
        zoom *= camera.data.ortho_scale / 2
    elif camera.data.type == "PANO":
        definitions["type"] = "environment"
    elif camera.data.type == "PERSP":
        definitions["type"] = "perspective"
        definitions["fieldofview"] = math.degrees(camera.data.angle)
        _depth_of_field(scene, definitions)
    else:
        raise NotImplementedError("Unknown camera.data.type")

    # Screenwindow
    view_camera_offset = list(context.region_data.view_camera_offset)

    if scene.render.use_border:
        xaspect, yaspect = utils.calc_aspect(scene.render.resolution_x, scene.render.resolution_y)
    else:
        xaspect, yaspect = utils.calc_aspect(context.region.width, context.region.height)

    offset_x = 2 * (view_camera_offset[0] * xaspect * 2)
    offset_y = 2 * (view_camera_offset[1] * yaspect * 2)

    definitions["screenwindow"] = utils.calc_screenwindow(zoom, camera.data.shift_x, camera.data.shift_y,
                                                          offset_x, offset_y, scene, context)


def _final(scene, definitions):
    camera = scene.camera
    lookat_orig, lookat_target, up_vector = _calc_lookat(camera.matrix_world)
    definitions["lookat.orig"] = lookat_orig
    definitions["lookat.target"] = lookat_target
    definitions["up"] = up_vector

    if camera.data.type == "ORTHO":
        type = "orthographic"
    elif camera.data.type == "PANO":
        type = "environment"
    else:
        type = "perspective"
    definitions["type"] = type

    # Field of view
    # Correction for vertical fit sensor, must truncate the float to .1f precision and round down
    width, height = utils.calc_filmsize_raw(scene)

    if camera.data.sensor_fit == "VERTICAL" and width > height:
        aspect_fix = round(width / height - 0.05, 1)  # make sure it rounds down
    else:
        aspect_fix = 1.0

    if type == "perspective":
        definitions["fieldofview"] = math.degrees(camera.data.angle * aspect_fix)
        _depth_of_field(scene, definitions)

    # screenwindow (for border rendering and camera shift)
    zoom = 1
    definitions["screenwindow"] = utils.calc_screenwindow(zoom, camera.data.shift_x, camera.data.shift_y, 0, 0, scene)


def _depth_of_field(scene, definitions):
    camera = scene.camera

    if not camera.data.luxcore.use_dof:
        return

    definitions["lensradius"] = (camera.data.lens / 1000) / (2 * camera.data.luxcore.fstop)

    if camera.data.luxcore.use_autofocus:
        definitions["autofocus.enable"] = True
    else:
        worldscale = utils.get_worldscale(scene, as_scalematrix=False)
        dof_obj = camera.data.dof_object

        if dof_obj:
            definitions["focaldistance"] = (camera.location - dof_obj.location).length * worldscale
        else:
            definitions["focaldistance"] = camera.data.dof_distance * worldscale


def _clipping(scene, definitions):
    camera = scene.camera
    if camera.data.luxcore.use_clipping:
        worldscale = utils.get_worldscale(scene, as_scalematrix=False)
        definitions["cliphither"] = camera.data.clip_start * worldscale
        definitions["clipyon"] = camera.data.clip_end * worldscale


def _clipping_plane(scene, definitions):
    cam_settings = scene.camera.data.luxcore

    if cam_settings.use_clipping_plane and cam_settings.clipping_plane:
        plane = cam_settings.clipping_plane
        normal = plane.rotation_euler.to_matrix() * Vector((0, 0, 1))

        definitions.update({
            "clippingplane.enable": cam_settings.use_clipping_plane,
            "clippingplane.center": list(plane.location),
            "clippingplane.normal": list(normal),
        })
    else:
        definitions["clippingplane.enable"] = False


def _motion_blur(definitions):
    pass # TODO
    # "shutteropen": shutter_open,
    # "shutterclose": shutter_close,


def _calc_lookat(cam_matrix):
    lookat_orig = list(cam_matrix.to_translation())
    lookat_target = list(cam_matrix * Vector((0, 0, -1)))
    up_vector = list(cam_matrix.to_3x3() * Vector((0, 1, 0)))
    return lookat_orig, lookat_target, up_vector
