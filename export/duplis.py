from ..bin import pyluxcore
from .. import utils
from . import blender_object
from time import time
from array import array


class Duplis:
    def __init__(self, exported_obj, matrix):
        self.exported_obj = exported_obj
        self.matrices = matrix
        self.count = 1

    def add(self, matrix):
        self.matrices += matrix
        self.count += 1


def convert(blender_obj, scene, context, luxcore_scene, engine):
    assert blender_obj.is_duplicator

    dupli_props = pyluxcore.Properties()
    start = time()

    mode = 'VIEWPORT' if context else 'RENDER'
    blender_obj.dupli_list_create(scene, settings=mode)

    name_prefix = utils.get_unique_luxcore_name(blender_obj)
    exported_duplis = {}

    dupli_count = len(blender_obj.dupli_list)
    for i, dupli in enumerate(blender_obj.dupli_list):
        # Use the utils functions to build names so linked objects work (libraries)
        name = name_prefix + utils.get_unique_luxcore_name(dupli.object)
        matrix_list = utils.matrix_to_list(dupli.matrix, scene, apply_worldscale=True)

        try:
            # Already exported, just update the Duplis info
            exported_duplis[name].add(matrix_list)
        except KeyError:
            # Not yet exported
            name_suffix = name_prefix + str(dupli.index)
            if dupli.particle_system:
                name_suffix += utils.to_luxcore_name(dupli.particle_system.name)

            obj_props, exported_obj = blender_object.convert(dupli.object, scene, context, luxcore_scene,
                                                             update_mesh=True, dupli_suffix=name_suffix)
            dupli_props.Set(obj_props)
            exported_duplis[name] = Duplis(exported_obj, matrix_list)

        # Report progress and check if user wants to cancel export
        if i % 1000 == 0:
            progress = (i / dupli_count) * 100
            engine.update_stats("Export", "Object: %s (Duplis: %d%%)" % (blender_obj.name, progress))

            if engine.test_break():
                blender_obj.dupli_list_clear()
                return

    blender_obj.dupli_list_clear()
    # Need to parse so we have the dupli objects available for DuplicateObject
    luxcore_scene.Parse(dupli_props)

    for duplis in exported_duplis.values():
        # Objects might be split if they have multiple materials
        for src_name in duplis.exported_obj.luxcore_names:
            dst_name = src_name + "dupli"
            count = duplis.count
            transformations = array("f", duplis.matrices)
            luxcore_scene.DuplicateObject(src_name, dst_name, count, transformations)

            # TODO: support steps and times (motion blur)
            # steps = 0 # TODO
            # times = array("f", [])
            # luxcore_scene.DuplicateObject(src_name, dst_name, count, steps, times, transformations)

    print("Dupli export took %.3fs" % (time() - start))
