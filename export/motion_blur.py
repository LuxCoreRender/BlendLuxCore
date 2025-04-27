import math
import pyluxcore
from .. import utils
from .caches.exported_data import ExportedObject, ExportedLight


# TODO fix motion blur of area lights, they get a wrong transformation

def convert(context, engine, scene, depsgraph, exported_objects):
    assert scene.camera
    motion_blur = scene.camera.data.luxcore.motion_blur
    assert motion_blur.enable and (motion_blur.object_blur or motion_blur.camera_blur)

    steps = motion_blur.steps
    assert steps >= 2 and isinstance(steps, int)

    frame_offsets = _calc_frame_offsets(motion_blur.shutter, steps)
    matrices = _get_matrices(context, engine, scene, steps, frame_offsets, depsgraph, exported_objects)

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
            transformation = utils.matrix_to_list(matrix)
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


def _get_matrices(context, engine, scene, steps, frame_offsets, depsgraph, exported_objects):
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
        if motion_blur.object_blur:
            _append_object_matrices(depsgraph, exported_objects, matrices, step)

        if motion_blur.camera_blur and not context:
            matrix = scene.camera.matrix_world

            prefix = "scene.camera."
            _append_matrix(matrices, prefix, matrix, step)

    # Restore original frame
    engine.frame_set(frame_center, subframe_center)
    return matrices


def _append_object_matrices(depsgraph, exported_objects, matrices, step):
    for dg_obj_instance in depsgraph.object_instances:
        obj = dg_obj_instance.parent if dg_obj_instance.is_instance else dg_obj_instance.object
        if not obj.luxcore.enable_motion_blur:
            continue

        obj_key = utils.make_key_from_instance(dg_obj_instance)
        matrix = dg_obj_instance.matrix_world.copy()

        try:
            exported_thing = exported_objects[obj_key]
            if isinstance(exported_thing, ExportedObject):
                for part in exported_thing.parts:
                    prefix = "scene.objects." + part.lux_obj + "."
                    _append_matrix(matrices, prefix, matrix, step)
            # else:
            #     assert isinstance(exported_thing, ExportedLight)
            #     prefix = "scene.lights." + exported_thing.lux_light_name + "."
            #     _append_matrix(matrices, prefix, matrix, step)
        except KeyError:
            # This is not a problem, objects are skipped during export for various reasons
            # E.g. if the object is not visible, or if it's a camera
            pass


def _append_matrix(matrices, prefix, matrix, step):
    if step == 0:
        matrices[prefix] = [matrix]
    else:
        matrices[prefix].append(matrix)
