import os
from ..bin import pyluxcore
from .. import utils
from ..utils import filesaver
from . import camera


def export(exporter, scene, exported_objects):
    original_frame = scene.frame_current
    original_subframe = scene.frame_subframe
    last_matrices = {}

    # TODO:
    # - remove transformation matrix on first frame for non-animated objects
    # - export all animated objects as instances (in utils.should_instance() or how it's called)
    # - make more generic so everything can be animated

    for frame in range(scene.frame_start, scene.frame_end + 1, scene.frame_step):
        scene.frame_set(frame, 0)
        props = pyluxcore.Properties()

        cam_props = camera.convert(exporter, scene)
        props.Set(cam_props)

        for obj in scene.objects:
            if not utils.use_instancing(obj, scene, None):
                # TODO this is a hack to get something usable fast
                continue

            key = utils.make_key(obj)
            matrix = obj.matrix_world
            try:
                last_matrix = last_matrices[key].copy()
            except KeyError:
                last_matrix = None

            last_matrices[key] = matrix.copy()

            if matrix == last_matrix:
                # Object transformation did not change since last frame
                continue

            try:
                exported_thing = exported_objects[key]

                for luxcore_name in exported_thing.luxcore_names:
                    # exported_objects contains instances of ExportedObject and ExportedLight
                    if isinstance(exported_thing, utils.ExportedObject):
                        prefix = "scene.objects." + luxcore_name + "."
                    else:
                        prefix = "scene.lights." + luxcore_name + "."

                    matrix_list = utils.matrix_to_list(matrix, scene, apply_worldscale=True)
                    props.Set(pyluxcore.Property(prefix + "transformation", matrix_list))
            except KeyError:
                # This is not a problem, objects are skipped during epxort for various reasons
                # E.g. if the object is not visible, or if it's a camera
                pass

        output_path, _ = utils.filesaver.get_output_path(scene, original_frame)
        filename = "%05d.scn" % frame
        dir_path = os.path.join(output_path, "anim")
        utils.create_dir_if_necessary(dir_path)
        with open(os.path.join(dir_path, filename), "w") as f:
            f.write(props.ToString())

    scene.frame_set(original_frame, original_subframe)
