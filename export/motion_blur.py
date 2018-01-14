import math
from mathutils import Matrix
from ..bin import pyluxcore
from .. import utils


def is_camera_moving(context, scene):
    motion_blur = scene.camera.data.luxcore.motion_blur
    steps = motion_blur.steps
    times = _calc_times(motion_blur.shutter, steps)
    # Step through time and collect camera matrices
    matrices = _get_matrices(context, scene, steps, times)
    cam_matrices = matrices["scene.camera."]
    # If all matrices are equal, the camera is not moving
    return not utils.all_elems_equal(cam_matrices)


def convert(context, scene, objects, exported_objects):
    assert scene.camera
    motion_blur = scene.camera.data.luxcore.motion_blur
    assert motion_blur.enable and (motion_blur.object_blur or motion_blur.camera_blur)

    steps = motion_blur.steps
    assert steps >= 2 and isinstance(steps, int)

    step_interval = motion_blur.shutter / (steps - 1)
    times = [step_interval * step - motion_blur.shutter * 0.5 for step in range(steps)]

    matrices = _get_matrices(context, scene, steps, times, objects, exported_objects)

    # Find and delete entries of non-moving objects (where all matrices are equal)
    for prefix, matrix_steps in list(matrices.items()):
        matrices_equal = utils.all_elems_equal(matrix_steps)

        if matrices_equal:
            # This object does not need motion blur because it does not move
            del matrices[prefix]

    # Export the properties for moving objects
    props = pyluxcore.Properties()

    for prefix, matrix_steps in matrices.items():
        for step in range(steps):
            time = times[step]
            matrix = matrix_steps[step]
            transformation = utils.matrix_to_list(matrix, scene, apply_worldscale=True)
            definitions = {
                "motion.%d.time" % step: time,
                "motion.%d.transformation" % step: transformation,
            }
            props.Set(utils.create_props(prefix, definitions))

    return props


def _calc_times(shutter, steps):
    step_interval = shutter / (steps - 1)
    times = [step_interval * step - shutter * 0.5 for step in range(steps)]
    return times


def _get_matrices(context, scene, steps, times, objects=None, exported_objects=None):
    motion_blur = scene.camera.data.luxcore.motion_blur
    matrices = {}  # {prefix: [matrix1, matrix2, ...]}

    frame_center = scene.frame_current
    subframe_center = scene.frame_subframe

    for step in range(steps):
        offset = times[step]
        time = frame_center + subframe_center + offset
        frame = math.floor(time)
        subframe = time - frame
        scene.frame_set(frame, subframe)

        if motion_blur.object_blur and objects and exported_objects:
            _append_object_matrices(objects, exported_objects, matrices, step)

        if motion_blur.camera_blur and not context:
            matrix = scene.camera.matrix_world.inverted()
            prefix = "scene.camera."
            _append_matrix(matrices, prefix, matrix, step)

    # Restore original frame
    scene.frame_set(frame_center, subframe_center)
    return matrices


def _append_object_matrices(objects, exported_objects, matrices, step):
    for obj in objects:
        if obj.type == "LAMP" and obj.data.type == "AREA":
            # TODO: Area lights need special matrix calculation
            continue

        key = utils.make_key(obj)

        try:
            exported_thing = exported_objects[key]

            for luxcore_name in exported_thing.luxcore_names:
                # exported_objects contains instances of ExportedObject and ExportedLight
                if isinstance(exported_thing, utils.ExportedObject):
                    prefix = "scene.objects." + luxcore_name + "."
                else:
                    prefix = "scene.lights." + luxcore_name + "."

                matrix = obj.matrix_world.copy()
                _append_matrix(matrices, prefix, matrix, step)
        except KeyError:
            # This is not a problem, objects are skipped during epxort for various reasons
            # E.g. if the object is not visible, or if it's a camera
            pass


def _append_matrix(matrices, prefix, matrix, step):
    if step == 0:
        matrices[prefix] = [matrix]
    else:
        matrices[prefix].append(matrix)
