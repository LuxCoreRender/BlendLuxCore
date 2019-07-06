import bpy
from ... import utils
from .. import mesh_converter
from .exported_data import ExportedObject
from .. import light

MESH_OBJECTS = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
EXPORTABLE_OBJECTS = MESH_OBJECTS | {"LIGHT", "EMPTY"}


class ObjectCache2:
    def __init__(self):
        self.exported_objects = {}
        self.exported_meshes = {}

    def first_run(self, exporter, depsgraph, engine, luxcore_scene, scene_props, is_viewport_render):
        # TODO use luxcore_scene.DuplicateObjects for instances
        for index, dg_obj_instance in enumerate(depsgraph.object_instances, start=1):
            obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
            if not self._is_visible(dg_obj_instance, obj):
                continue

            self._convert_obj(exporter, dg_obj_instance, obj, depsgraph,
                              luxcore_scene, scene_props, is_viewport_render)
            if engine:
                # Objects are the most expensive to export, so they dictate the progress
                # engine.update_progress(index / obj_amount)
                if engine.test_break():
                    return False

        self._debug_info()
        return True

    def _debug_info(self):
        print("Objects in cache:", len(self.exported_objects))
        print("Meshes in cache:", len(self.exported_meshes))
        for key, exported_mesh in self.exported_meshes.items():
            if exported_mesh:
                print(key, exported_mesh.mesh_definitions)
            else:
                print(key, "mesh is None")

    def _is_visible(self, dg_obj_instance, obj):
        return dg_obj_instance.show_self and obj.type in EXPORTABLE_OBJECTS

    def _get_mesh_key(self, obj, is_viewport_render=True):
        # Important: we need the data of the original object, not the evaluated one
        return utils.get_luxcore_name(obj.original.data, is_viewport_render)

    def _convert_obj(self, exporter, dg_obj_instance, obj, depsgraph, luxcore_scene, scene_props, is_viewport_render):
        """ Convert one DepsgraphObjectInstance amd keep track of it """
        if obj.type == "EMPTY" or obj.data is None:
            return

        obj_key = utils.make_key_from_instance(dg_obj_instance)

        if obj.type in MESH_OBJECTS:
            if obj_key in self.exported_objects:
                raise Exception("key already in exp_obj:", obj_key)
            self._convert_mesh_obj(dg_obj_instance, obj, obj_key, depsgraph, luxcore_scene,
                                   scene_props, is_viewport_render)
        elif obj.type == "LIGHT":
            props, exported_stuff = light.convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene,
                                                        dg_obj_instance.matrix_world.copy(), is_viewport_render)
            if exported_stuff:
                self.exported_objects[obj_key] = exported_stuff
                scene_props.Set(props)

    def _convert_mesh_obj(self, dg_obj_instance, obj, obj_key, depsgraph,
                          luxcore_scene, scene_props, is_viewport_render):
        transform = dg_obj_instance.matrix_world

        use_instancing = is_viewport_render or dg_obj_instance.is_instance or utils.can_share_mesh(obj)
        mesh_key = self._get_mesh_key(obj, is_viewport_render)

        if use_instancing and mesh_key in self.exported_meshes:
            print("retrieving mesh from cache")
            exported_mesh = self.exported_meshes[mesh_key]
        else:
            print("fresh export")
            exported_mesh = mesh_converter.convert(obj, mesh_key, depsgraph, luxcore_scene,
                                                   is_viewport_render, use_instancing, transform)
            self.exported_meshes[mesh_key] = exported_mesh

        if exported_mesh:
            obj_transform = transform.copy() if use_instancing else None
            exported_obj = ExportedObject(obj_key, exported_mesh.mesh_definitions, obj_transform)
            if exported_obj:
                scene_props.Set(exported_obj.get_props())
                self.exported_objects[obj_key] = exported_obj

    def diff(self, depsgraph):
        return depsgraph.id_type_updated("OBJECT")

    def update(self, exporter, depsgraph, luxcore_scene, scene_props, is_viewport_render=True):
        print("object cache update")

        # TODO maybe not loop over all instances, instead only loop over updated
        #  objects and check if they have a particle system that needs to be updated?
        #  Would be better for performance with many particles, however I'm not sure
        #  we can find all instances corresponding to one particle system?

        # For now, transforms and new instances only
        for dg_obj_instance in depsgraph.object_instances:
            obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
            if not self._is_visible(dg_obj_instance, obj):
                continue

            obj_key = utils.make_key_from_instance(dg_obj_instance)
            transform = dg_obj_instance.matrix_world.copy()

            if obj_key in self.exported_objects and obj.type != "LIGHT":
                exported_obj = self.exported_objects[obj_key]
                last_transform = exported_obj.transform
                if last_transform != transform:
                    # Update transform
                    exported_obj.transform = transform
                    scene_props.Set(exported_obj.get_props())
            else:
                # Object is new and not in LuxCore yet, or it is a light, do a full export
                # TODO use luxcore_scene.DuplicateObjects for instances
                self._convert_obj(exporter, dg_obj_instance, obj, depsgraph,
                                  luxcore_scene, scene_props, is_viewport_render)

        # Geometry updates (mesh edit, modifier edit etc.)
        if depsgraph.id_type_updated("OBJECT"):
            print("exported meshes:", self.exported_meshes.keys())

            for dg_update in depsgraph.updates:
                print(f"update id: {dg_update.id}, geom: {dg_update.is_updated_geometry}, trans: {dg_update.is_updated_transform}")

                if dg_update.is_updated_geometry and isinstance(dg_update.id, bpy.types.Object):
                    obj = dg_update.id
                    obj_key = utils.make_key(obj)

                    if obj.type in MESH_OBJECTS:
                        print(f"Geometry of obj {obj.name} was updated")
                        mesh_key = self._get_mesh_key(obj)
                        if mesh_key not in self.exported_meshes:
                            # Debug
                            raise Exception("NO MESH KEY FOUND")
                        transform = None  # In viewport render, everything is instanced
                        use_instancing = True
                        exported_mesh = mesh_converter.convert(obj, mesh_key, depsgraph, luxcore_scene,
                                                               is_viewport_render, use_instancing, transform)
                        self.exported_meshes[mesh_key] = exported_mesh
                        print(self.exported_meshes[mesh_key].mesh_definitions)
                    elif obj.type == "LIGHT":
                        print(f"Light obj {obj.name} was updated")
                        props, exported_stuff = light.convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene,
                                                                    obj.matrix_world.copy(), is_viewport_render)
                        if exported_stuff:
                            self.exported_objects[obj_key] = exported_stuff
                            scene_props.Set(props)

        self._debug_info()
