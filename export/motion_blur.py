import math
from ..bin import pyluxcore
from .. import utils


def convert(scene, objects, exported_objects):
    assert scene.camera
    motion_blur = scene.camera.data.luxcore.motion_blur

    steps = motion_blur.steps
    assert steps > 1

    step_interval = motion_blur.shutter / (steps - 1)
    times = [step_interval * step - motion_blur.shutter * 0.5 for step in range(steps)]

    matrices = _get_matrices(scene, objects, exported_objects, steps, times)

    # Find and delete entries of non-moving objects (where all matrices are equal)
    for prefix, matrix_steps in list(matrices.items()):
        # https://stackoverflow.com/a/10285205
        first = matrix_steps[0]
        matrices_equal = all(matrix == first for matrix in matrix_steps)

        if matrices_equal:
            # This object does not need motion blur because it does not move
            del matrices[prefix]

    # Export the properties for moving objects
    props = pyluxcore.Properties()

    for prefix, matrix_steps in matrices.items():
        for step in range(steps):
            time = times[step]
            matrix = matrix_steps[step]
            transformation = utils.matrix_to_list(matrix, scene, apply_worldscale=True, invert=True)
            definitions = {
                "motion.%d.time" % step: time,
                "motion.%d.transformation" % step: transformation,
            }
            props.Set(utils.create_props(prefix, definitions))

    return props


def _get_matrices(scene, objects, exported_objects, steps, times):
    matrices = {}  # {prefix: [matrix1, matrix2, ...]}

    frame_center = scene.frame_current
    subframe_center = scene.frame_subframe

    for step in range(steps):
        offset = times[step]
        time = frame_center + subframe_center + offset
        frame = math.floor(time)
        subframe = time - frame
        scene.frame_set(frame, subframe)

        for obj in objects:
            if obj.type == "LAMP" and obj.data.type == "AREA":
                # TODO: Area lights need special matrix calculation
                continue

            key = utils.make_key(obj)

            try:
                exported_thing = exported_objects[key]
            except KeyError:
                # This is not a problem, objects are skipped during epxort for various reasons
                continue

            matrix = obj.matrix_world.copy()

            for luxcore_name in exported_thing.luxcore_names:
                # exported_objects contains instances of ExportedObject and ExportedLight
                if isinstance(exported_thing, utils.ExportedObject):
                    prefix = "scene.objects." + luxcore_name + "."
                else:
                    prefix = "scene.lights." + luxcore_name + "."

                if step == 0:
                    matrices[prefix] = [matrix]
                else:
                    matrices[prefix].append(matrix)

    # Restore original frame
    scene.frame_set(frame_center, subframe_center)
    return matrices
