import math
from mathutils import Vector, Matrix
from ..bin import pyluxcore
from .. import utils
from ..nodes.output import get_active_output


def convert(exporter, scene, context=None, is_camera_moving=False):
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
            _clipping(scene, definitions)
        else:
            raise NotImplementedError("Unknown context.region_data.view_perspective")
    else:
        # Final render
        _final(scene, definitions)
        _clipping(scene, definitions)

    _clipping_plane(scene, definitions)
    _motion_blur(scene, definitions, context, is_camera_moving)

    cam_props = utils.create_props(prefix, definitions)
    cam_props.Set(_get_volume_props(exporter, scene))
    return cam_props


def _view_ortho(scene, context, definitions):
    cam_matrix = Matrix(context.region_data.view_matrix).inverted()
    lookat_orig, lookat_target, up_vector = _calc_lookat(cam_matrix, scene)
    world_scale = utils.get_worldscale(scene, False)

    definitions["type"] = "orthographic"
    zoom = 0.915 * world_scale * context.region_data.view_distance * 35 / context.space_data.lens

    # Move the camera origin away from the viewport center to avoid clipping
    origin = Vector(lookat_orig)
    target = Vector(lookat_target)
    origin += (origin - target) * 50
    definitions["lookat.orig"] = list(origin)
    definitions["lookat.target"] = lookat_target
    definitions["up"] = up_vector

    definitions["screenwindow"] = utils.calc_screenwindow(zoom, 0, 0, scene, context)


def _view_persp(scene, context, definitions):
    cam_matrix = Matrix(context.region_data.view_matrix).inverted()
    lookat_orig, lookat_target, up_vector = _calc_lookat(cam_matrix, scene)
    definitions["lookat.orig"] = lookat_orig
    definitions["lookat.target"] = lookat_target
    definitions["up"] = up_vector

    definitions["type"] = "perspective"
    zoom = 2
    definitions["fieldofview"] = math.degrees(2 * math.atan(16 / context.space_data.lens))

    definitions["screenwindow"] = utils.calc_screenwindow(zoom, 0, 0, scene, context)


def _view_camera(scene, context, definitions):
    camera = scene.camera

    if camera.type != "CAMERA":
        raise Exception("%s Objects as cameras are not supported, use a CAMERA object" % camera.type)

    lookat_orig, lookat_target, up_vector = _calc_lookat(camera.matrix_world, scene)
    world_scale = utils.get_worldscale(scene, False)
    
    definitions["lookat.orig"] = lookat_orig
    definitions["lookat.target"] = lookat_target
    definitions["up"] = up_vector
    
    # Magic zoom formula for camera viewport zoom from Cycles export code
    zoom = 4 / ((math.sqrt(2) + context.region_data.view_camera_zoom / 50) ** 2)

    if camera.data.type == "ORTHO":
        definitions["type"] = "orthographic"
        zoom *= 0.5 * world_scale * camera.data.ortho_scale
    elif camera.data.type == "PANO":
        definitions["type"] = "environment"
    elif camera.data.type == "PERSP":
        definitions["type"] = "perspective"
        definitions["fieldofview"] = math.degrees(camera.data.angle)
        _depth_of_field(scene, definitions)
    else:
        raise NotImplementedError("Unknown camera.data.type")

    # Screenwindow
    definitions["screenwindow"] = utils.calc_screenwindow(zoom, camera.data.shift_x, camera.data.shift_y, scene, context)


def _final(scene, definitions):
    camera = scene.camera

    if camera.type != "CAMERA":
        raise Exception("%s Objects as cameras are not supported, use a CAMERA object" % camera.type)

    lookat_orig, lookat_target, up_vector = _calc_lookat(camera.matrix_world, scene)
    world_scale = utils.get_worldscale(scene, False)
    definitions["lookat.orig"] = lookat_orig
    definitions["lookat.target"] = lookat_target
    definitions["up"] = up_vector
    zoom = 1

    if camera.data.type == "ORTHO":
        cam_type = "orthographic"
        zoom = 0.5 * world_scale * camera.data.ortho_scale

    elif camera.data.type == "PANO":
        cam_type = "environment"
    else:
        cam_type = "perspective"
    definitions["type"] = cam_type

    # Field of view
    if cam_type == "perspective":
        definitions["fieldofview"] = math.degrees(camera.data.angle)
        _depth_of_field(scene, definitions)

    # screenwindow (for border rendering and camera shift)
    definitions["screenwindow"] = utils.calc_screenwindow(zoom, camera.data.shift_x, camera.data.shift_y, scene)


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
            # Use distance along camera Z direction
            cam_matrix = camera.matrix_world
            lookat_orig = cam_matrix.to_translation()
            lookat_target = cam_matrix * Vector((0, 0, -1))

            lookat_dir = (lookat_target - lookat_orig).normalized()
            dof_dir = dof_obj.matrix_world.to_translation() - lookat_orig

            definitions["focaldistance"] = abs(lookat_dir.dot(dof_dir)) * worldscale
        else:
            definitions["focaldistance"] = camera.data.dof_distance * worldscale


def _clipping(scene, definitions):
    camera = scene.camera
    if not utils.is_valid_camera(camera):
        # Viewport render should work without camera
        return

    if camera.data.luxcore.use_clipping:
        worldscale = utils.get_worldscale(scene, as_scalematrix=False)
        clip_start = camera.data.clip_start * worldscale
        clip_end = camera.data.clip_end * worldscale

        definitions["cliphither"] = clip_start
        definitions["clipyon"] = clip_end

        # Show a warning if the clip settings don't make sense
        warning = ""
        if clip_start > clip_end:
            warning = "Clip start greater than clip end"
        if clip_start == clip_end:
            warning = "Clip start and clip end are exactly equal"

        if warning:
            msg = 'Camera: %s' % warning
            scene.luxcore.errorlog.add_warning(msg, obj_name=camera.name)


def _clipping_plane(scene, definitions):
    if not utils.is_valid_camera(scene.camera):
        # Viewport render should work without camera
        return
    cam_settings = scene.camera.data.luxcore

    if cam_settings.use_clipping_plane and cam_settings.clipping_plane:
        plane = cam_settings.clipping_plane
        normal = plane.rotation_euler.to_matrix() * Vector((0, 0, 1))
        worldscale = utils.get_worldscale(scene, as_scalematrix=False)

        definitions.update({
            "clippingplane.enable": cam_settings.use_clipping_plane,
            "clippingplane.center": list(plane.location * worldscale),
            "clippingplane.normal": list(normal),
        })
    else:
        definitions["clippingplane.enable"] = False


def _motion_blur(scene, definitions, context, is_camera_moving):
    if not utils.is_valid_camera(scene.camera):
        # Viewport render should work without camera
        return

    moblur_settings = scene.camera.data.luxcore.motion_blur
    if not moblur_settings.enable:
        return

    definitions["shutteropen"] = -moblur_settings.shutter / 2
    definitions["shutterclose"] = moblur_settings.shutter / 2

    # Don't export camera blur in viewport render
    if moblur_settings.camera_blur and not context and is_camera_moving:
        # Make sure lookup is defined - this function should be the last to modify it
        assert "lookat.orig" in definitions
        assert "lookat.target" in definitions
        assert "up" in definitions
        # Reset lookat - it's handled by motion.x.transformation
        definitions["lookat.orig"] = [0, 0, 0]
        definitions["lookat.target"] = [0, 0, -1]
        definitions["up"] = [0, 1, 0]
        # Note: camera motion system is defined in export/motion_blur.py


def _calc_lookat(cam_matrix, scene):
    cam_matrix = utils.get_scaled_to_world(cam_matrix, scene)
    lookat_orig = list(cam_matrix.to_translation())
    lookat_target = list(cam_matrix * Vector((0, 0, -1)))
    up_vector = list(cam_matrix.to_3x3() * Vector((0, 1, 0)))
    return lookat_orig, lookat_target, up_vector


def _get_volume_props(exporter, scene):
    props = pyluxcore.Properties()

    if not utils.is_valid_camera(scene.camera):
        # Viewport render should work without camera
        return props

    cam_settings = scene.camera.data.luxcore
    volume_node_tree = cam_settings.volume

    if volume_node_tree:
        luxcore_name = utils.get_luxcore_name(volume_node_tree)
        active_output = get_active_output(volume_node_tree)

        try:
            active_output.export(exporter, props, luxcore_name)
            props.Set(pyluxcore.Property("scene.camera.volume", luxcore_name))
        except Exception as error:
            msg = 'Camera: %s' % error
            scene.luxcore.errorlog.add_warning(msg, obj_name=scene.camera.name)

    props.Set(pyluxcore.Property("scene.camera.autovolume.enable", cam_settings.auto_volume))
    return props
