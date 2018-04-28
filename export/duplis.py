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


def convert(exporter, blender_obj, scene, context, luxcore_scene, engine=None):
    """
    Converts particle systems and dupliverts/faces (everything apart from hair)
    """
    try:
        assert blender_obj.is_duplicator

        dupli_props = pyluxcore.Properties()

        if not utils.is_obj_visible(blender_obj, scene, context):
            # Emitter is not on a visible layer
            return

        start = time()

        mode = 'VIEWPORT' if context else 'RENDER'
        blender_obj.dupli_list_create(scene, settings=mode)

        name_prefix = utils.get_luxcore_name(blender_obj, context)
        exported_duplis = {}
        non_invertible_count = 0

        dupli_count = len(blender_obj.dupli_list)
        for i, dupli in enumerate(blender_obj.dupli_list):
            # Metaballs are omitted from this loop, they cause glitches.
            if dupli.object.type == "META":
                continue

            if dupli.matrix.determinant() == 0:
                # We can handle non-invertible matrices (a small epsilon is added)
                # but warn the user later because it's a sign of trouble
                non_invertible_count += 1

            # Use the utils functions to build names so linked objects work (libraries)
            name = name_prefix + utils.get_luxcore_name(dupli.object, context)
            matrix_list = utils.matrix_to_list(dupli.matrix, scene, apply_worldscale=True)

            if dupli.object.type == "LAMP" and not dupli.object.data.type == "AREA":
                # It is a light
                name_suffix = _get_name_suffix(name_prefix, dupli, context)
                light_props, exported_light = blender_object.convert(exporter, dupli.object, scene, context, luxcore_scene,
                                                                     update_mesh=True, dupli_suffix=name_suffix)
                for luxcore_name in exported_light.luxcore_names:
                    key = "scene.lights." + luxcore_name + ".transformation"
                    light_props.Set(pyluxcore.Property(key, matrix_list))

                dupli_props.Set(light_props)
            else:
                # It is an object or area light
                try:
                    # Already exported, just update the Duplis info
                    exported_duplis[name].add(matrix_list)
                except KeyError:
                    # Not yet exported
                    name_suffix = _get_name_suffix(name_prefix, dupli, context)
                    obj_props, exported_obj = blender_object.convert(exporter, dupli.object, scene, context, luxcore_scene,
                                                                     update_mesh=True, dupli_suffix=name_suffix)
                    dupli_props.Set(obj_props)
                    exported_duplis[name] = Duplis(exported_obj, matrix_list)

            # Report progress and check if user wants to cancel export
            # Note: in viewport render we can't do all this, so we don't pass the engine there
            if engine and i % 1000 == 0:
                progress = (i / dupli_count) * 100
                engine.update_stats("Export", "Object: %s (Duplis: %d%%)" % (blender_obj.name, progress))

                if engine.test_break():
                    blender_obj.dupli_list_clear()
                    return

        if non_invertible_count:
            msg = (
                '%d duplis with non-invertible matrices on duplicator "%s". '
                'This can happen if e.g. the scale is 0' % (non_invertible_count, blender_obj.name)
            )
            scene.luxcore.errorlog.add_warning(msg)

        blender_obj.dupli_list_clear()
        # Need to parse so we have the dupli objects available for DuplicateObject
        luxcore_scene.Parse(dupli_props)

        # We have to invalidate the node cache because we have defined materials in
        # the dupli_props which are not defined in the main scene props (so if
        # another material tries to use the cached name, it will result in default
        # grey matte because the name is not in the main properties)
        exporter.node_cache.clear()

        for duplis in exported_duplis.values():
            # exported_obj sometimes is None, e.g. when instancing a group using an empty
            exported_obj = duplis.exported_obj

            if exported_obj:
                # exported_objects should only contain instances of ExportedObject
                assert isinstance(exported_obj, utils.ExportedObject)

                # Objects might be split if they have multiple materials
                for src_name in exported_obj.luxcore_names:
                    dst_name = src_name + "dupli"
                    count = duplis.count
                    transformations = array("f", duplis.matrices)
                    luxcore_scene.DuplicateObject(src_name, dst_name, count, transformations)

                    # TODO: support steps and times (motion blur)
                    # steps = 0 # TODO
                    # times = array("f", [])
                    # luxcore_scene.DuplicateObject(src_name, dst_name, count, steps, times, transformations)

                    # Delete the object we used for duplication, we don't want it to show up in the scene
                    luxcore_scene.DeleteObject(src_name)

        print("Dupli export took %.3f s" % (time() - start))
    except Exception as error:
        msg = '[Duplicator "%s"] %s' % (blender_obj.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()


def _get_name_suffix(name_prefix, dupli, context):
    name_suffix = name_prefix + str(dupli.index)
    if dupli.particle_system:
        name_suffix += utils.get_luxcore_name(dupli.particle_system, context)
    return name_suffix
