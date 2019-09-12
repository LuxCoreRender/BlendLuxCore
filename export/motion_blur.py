import math
from ..bin import pyluxcore
from .. import utils
from .caches.exported_data import ExportedObject


# TODO fix motion blur of area lights, they get a wrong transformation

def convert(context, engine, scene, depsgraph, object_cache2):
    assert scene.camera
    motion_blur = scene.camera.data.luxcore.motion_blur
    assert motion_blur.enable and (motion_blur.object_blur or motion_blur.camera_blur)

    steps = motion_blur.steps
    assert steps >= 2 and isinstance(steps, int)

    frame_offsets = _calc_frame_offsets(motion_blur.shutter, steps)
    matrices = _get_matrices(context, engine, scene, steps, frame_offsets, depsgraph, object_cache2)

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
            time = frame_offsets[step]
            matrix = matrix_steps[step]
            transformation = utils.matrix_to_list(matrix, scene, apply_worldscale=True)
            definitions = {
                "motion.%d.time" % step: time,
                "motion.%d.transformation" % step: transformation,
            }
            props.Set(utils.create_props(prefix, definitions))

    # We need this information outside
    is_camera_moving = "scene.camera." in matrices
    return props, is_camera_moving


def _calc_frame_offsets(shutter, steps):
    """ Return a list of offsets (unit: frame) to step through in _get_matrices() """
    step_interval = shutter / (steps - 1)
    return [step_interval * step - shutter / 2 for step in range(steps)]


def _get_matrices(context, engine, scene, steps, frame_offsets, depsgraph=None, object_cache2=None):
    motion_blur = scene.camera.data.luxcore.motion_blur
    matrices = {}  # {prefix: [matrix1, matrix2, ...]}

    frame_center = scene.frame_current
    subframe_center = scene.frame_subframe
    for step in range(steps):
        offset = frame_offsets[step]
        frame = frame_center + subframe_center + offset
        frame_int = math.floor(frame)
        subframe = frame - frame_int
        engine.frame_set(frame_int, subframe)
        if motion_blur.object_blur and depsgraph and object_cache2:
            _append_object_matrices(depsgraph, object_cache2, matrices, step)

        if motion_blur.camera_blur and not context:
            matrix = scene.camera.matrix_world

            prefix = "scene.camera."
            _append_matrix(matrices, prefix, matrix, step)

    # Restore original frame
    engine.frame_set(frame_center, subframe_center)
    return matrices


def _append_object_matrices(depsgraph, object_cache2, matrices, step):
    for index, dg_obj_instance in enumerate(depsgraph.object_instances, start=1):
        obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
        obj_key = utils.make_key_from_instance(dg_obj_instance)

        try:
            if obj_key in object_cache2.exported_objects:
                if isinstance(object_cache2.exported_objects[obj_key], ExportedObject) and obj.luxcore.enable_motion_blur:
                    for p in object_cache2.exported_objects[obj_key].parts:
                        luxcore_name = p.lux_obj
                        prefix = "scene.objects." + luxcore_name + "."
                        matrix = obj.matrix_world
                        _append_matrix(matrices, prefix, matrix, step)

        except KeyError:
            # This is not a problem, objects are skipped during export for various reasons
            # E.g. if the object is not visible, or if it's a camera
            pass


def _append_matrix(matrices, prefix, matrix, step):
    matrix = matrix.copy()
    if step == 0:
        matrices[prefix] = [matrix]
    else:
        matrices[prefix].append(matrix)
