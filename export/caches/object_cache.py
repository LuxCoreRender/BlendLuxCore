import bpy
from ... import utils
from ...bin import pyluxcore
from .. import mesh_converter
from ..hair import convert_hair
from .exported_data import ExportedObject
from .. import light

MESH_OBJECTS = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
EXPORTABLE_OBJECTS = MESH_OBJECTS | {"LIGHT"}


def get_material(obj, material_index, exporter, depsgraph, is_viewport_render):
    from ...utils.errorlog import LuxCoreErrorLog
    from ...utils import node as utils_node
    from .. import material
    if material_index < len(obj.material_slots):
        mat = obj.material_slots[material_index].material

        if mat is None:
            # Note: material.convert returns the fallback material in this case
            msg = "No material attached to slot %d" % (material_index + 1)
            LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)
    else:
        # The object has no material slots
        LuxCoreErrorLog.add_warning("No material defined", obj_name=obj.name)
        # Use fallback material
        mat = None

    if mat:
        use_pointiness = False
        if mat.luxcore.node_tree:
            # Check if a pointiness node exists, better check would be if the node is linked
            use_pointiness = len(utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexPointiness")) > 0
            imagemaps = utils_node.find_nodes(mat.luxcore.node_tree, "LuxCoreNodeTexImagemap")
            if imagemaps and not utils_node.has_valid_uv_map(obj):
                msg = (utils.pluralize("%d image texture", len(imagemaps)) + " used, but no UVs defined. "
                       "In case of bumpmaps this can lead to artifacts")
                LuxCoreErrorLog.add_warning(msg, obj_name=obj.name)

        lux_mat_name, mat_props = material.convert(exporter, depsgraph, mat, is_viewport_render, obj.name)
        return lux_mat_name, mat_props, use_pointiness
    else:
        lux_mat_name, mat_props = material.fallback()
        return lux_mat_name, mat_props, False

class ObjectCache2:
    def __init__(self):
        self.exported_objects = {}
        self.exported_meshes = {}

    def first_run(self, exporter, depsgraph, view_layer, engine, luxcore_scene, scene_props, is_viewport_render):
        # TODO use luxcore_scene.DuplicateObjects for instances
        for index, dg_obj_instance in enumerate(depsgraph.object_instances, start=1):
            obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
            if not (self._is_visible(dg_obj_instance, obj) or obj.visible_get(view_layer=view_layer)):
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
        # for key, exported_mesh in self.exported_meshes.items():
        #     if exported_mesh:
        #         print(key, exported_mesh.mesh_definitions)
        #     else:
        #         print(key, "mesh is None")

    def _is_visible(self, dg_obj_instance, obj):
        # TODO if this code needs to be used elsewhere (e.g. in material preview),
        #  move it to utils (it doesn't concern this cache class)
        return dg_obj_instance.show_self and obj.type in EXPORTABLE_OBJECTS

    def _get_mesh_key(self, obj, use_instancing, is_viewport_render=True):
        # Important: we need the data of the original object, not the evaluated one.
        # The instancing state has to be part of the key because a non-instanced mesh
        # has its transformation baked-in and can't be used by other instances.
        modified = utils.has_deforming_modifiers(obj.original)
        source = obj.original.data if (use_instancing and not modified) else obj.original
        key = utils.get_luxcore_name(source, is_viewport_render)
        if use_instancing:
            key += "_instance"
        return key

    def _convert_obj(self, exporter, dg_obj_instance, obj, depsgraph, luxcore_scene, scene_props, is_viewport_render):
        """ Convert one DepsgraphObjectInstance amd keep track of it """
        if obj.type == "EMPTY" or obj.data is None:
            return

        obj_key = utils.make_key_from_instance(dg_obj_instance)

        if obj.type in MESH_OBJECTS:
            # assert obj_key not in self.exported_objects
            self._convert_mesh_obj(exporter, dg_obj_instance, obj, obj_key, depsgraph,
                                   luxcore_scene, scene_props, is_viewport_render)
        elif obj.type == "LIGHT":
            props, exported_stuff = light.convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene,
                                                        dg_obj_instance.matrix_world.copy(), is_viewport_render)
            if exported_stuff:
                self.exported_objects[obj_key] = exported_stuff
                scene_props.Set(props)

        # Convert hair
        for psys in obj.particle_systems:
            settings = psys.settings

            if settings.type == "HAIR" and settings.render_type == "PATH":
                convert_hair(exporter, obj, psys, depsgraph, luxcore_scene, is_viewport_render)

    def _convert_mesh_obj(self, exporter, dg_obj_instance, obj, obj_key, depsgraph,
                          luxcore_scene, scene_props, is_viewport_render):
        transform = dg_obj_instance.matrix_world

        use_instancing = is_viewport_render or dg_obj_instance.is_instance or utils.can_share_mesh(obj.original)
        mesh_key = self._get_mesh_key(obj, use_instancing, is_viewport_render)
        # print(obj.name, "mesh key:", mesh_key)

        if use_instancing and mesh_key in self.exported_meshes:
            # print("retrieving mesh from cache")
            exported_mesh = self.exported_meshes[mesh_key]
        else:
            # print("fresh export")
            exported_mesh = mesh_converter.convert(obj, mesh_key, depsgraph, luxcore_scene,
                                                   is_viewport_render, use_instancing, transform)
            self.exported_meshes[mesh_key] = exported_mesh

        if exported_mesh:
            mat_names = []
            for idx, (shape_name, mat_index) in enumerate(exported_mesh.mesh_definitions):
                lux_mat_name, mat_props, use_pointiness = get_material(obj, mat_index, exporter, depsgraph, is_viewport_render)
                scene_props.Set(mat_props)
                mat_names.append(lux_mat_name)

                if use_pointiness:
                    # Replace shape definition with pointiness shape
                    pointiness_shape = shape_name + "_pointiness"
                    prefix = "scene.shapes." + pointiness_shape + "."
                    scene_props.Set(pyluxcore.Property(prefix + "type", "pointiness"))
                    scene_props.Set(pyluxcore.Property(prefix + "source", shape_name))
                    exported_mesh.mesh_definitions[idx] = [pointiness_shape, mat_index]

            obj_transform = transform.copy() if use_instancing else None

            if obj.luxcore.id == -1:
                obj_id = utils.make_object_id(dg_obj_instance)
            else:
                obj_id = obj.luxcore.id

            exported_obj = ExportedObject(obj_key, exported_mesh.mesh_definitions, mat_names,
                                          obj_transform, obj.luxcore.visible_to_camera, obj_id)
            scene_props.Set(exported_obj.get_props())
            self.exported_objects[obj_key] = exported_obj


    def diff(self, depsgraph):
        only_scene = len(depsgraph.updates) == 1 and isinstance(depsgraph.updates[0].id, bpy.types.Scene)
        return depsgraph.id_type_updated("OBJECT") and not only_scene

    def update(self, exporter, depsgraph, luxcore_scene, scene_props, is_viewport_render=True):
        print("object cache update")

        # TODO maybe not loop over all instances, instead only loop over updated
        #  objects and check if they have a particle system that needs to be updated?
        #  Would be better for performance with many particles, however I'm not sure
        #  we can find all instances corresponding to one particle system?

        # Currently, every update that doesn't require a mesh re-export happens here
        for dg_obj_instance in depsgraph.object_instances:
            obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
            if not self._is_visible(dg_obj_instance, obj):
                continue

            obj_key = utils.make_key_from_instance(dg_obj_instance)

            if obj_key in self.exported_objects and obj.type != "LIGHT":
                exported_obj = self.exported_objects[obj_key]
                updated = False

                if exported_obj.transform != dg_obj_instance.matrix_world:
                    exported_obj.transform = dg_obj_instance.matrix_world.copy()
                    updated = True

                obj_id = utils.make_object_id(dg_obj_instance)
                if exported_obj.obj_id != obj_id:
                    exported_obj.obj_id = obj_id
                    updated = True

                if exported_obj.visible_to_camera != obj.luxcore.visible_to_camera:
                    exported_obj.visible_to_camera = obj.luxcore.visible_to_camera
                    updated = True

                if updated:
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
                        use_instancing = True
                        mesh_key = self._get_mesh_key(obj, use_instancing)
                        if mesh_key not in self.exported_meshes:
                            # Debug
                            raise Exception("NO MESH KEY FOUND")
                        transform = None  # In viewport render, everything is instanced
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
