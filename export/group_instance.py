from . import blender_object
from .. import utils


def convert(exporter, duplicator, scene, context, luxcore_scene, props):
    try:
        assert duplicator.is_duplicator
        assert duplicator.dupli_type == "GROUP"

        if not utils.is_obj_visible(duplicator, scene, context):
            # Duplicator is not on a visible layer
            return

        dupli_suffix = utils.get_luxcore_name(duplicator, context)

        mode = 'VIEWPORT' if context else 'RENDER'
        duplicator.dupli_list_create(scene, settings=mode)

        for dupli_obj in duplicator.dupli_list:
            obj = dupli_obj.object
            if dupli_obj.matrix.determinant() == 0:
                continue

            if obj.type == "LAMP":
                # It is a light (we don't do instancing here)
                light_props, exported_light = blender_object.convert(exporter, obj, scene, context,
                                                                     luxcore_scene, update_mesh=True,
                                                                     dupli_suffix=dupli_suffix,
                                                                     dupli_matrix=dupli_obj.matrix)
                props.Set(light_props)
            else:
                # It is an object
                key = utils.make_key(duplicator.dupli_group) + utils.make_key(obj)

                try:
                    exported_obj = exporter.dupli_groups[key]
                except KeyError:
                    obj_props, exported_obj = blender_object.convert(exporter, obj, scene, context,
                                                                     luxcore_scene, update_mesh=True,
                                                                     dupli_suffix=dupli_suffix, duplicator=duplicator)
                    exporter.dupli_groups[key] = exported_obj

                if exported_obj:
                    mesh_definitions = exported_obj.mesh_definitions
                    is_shared_mesh = True
                    luxcore_name = utils.make_key(obj) + dupli_suffix
                    transform = utils.matrix_to_list(dupli_obj.matrix, scene, apply_worldscale=True)
                    blender_object.define_from_mesh_defs(mesh_definitions, scene, context, exporter, obj, props,
                                                         is_shared_mesh, luxcore_name, transform, duplicator)
    except Exception as error:
        msg = '[Dupli group "%s"] %s' % (duplicator.dupli_group.name, error)
        scene.luxcore.errorlog.add_warning(msg)
        import traceback
        traceback.print_exc()
    finally:
        duplicator.dupli_list_clear()
