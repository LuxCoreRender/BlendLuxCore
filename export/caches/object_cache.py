import bpy
from array import array

from ... import utils
from ...bin import pyluxcore
from .. import mesh_converter
from ..hair import convert_hair, warn_about_missing_uvs
from .exported_data import ExportedObject, ExportedPart
from .. import light, material
from ...utils.errorlog import LuxCoreErrorLog
from ...utils import node as utils_node
from ...nodes.output import get_active_output

MESH_OBJECTS = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
EXPORTABLE_OBJECTS = MESH_OBJECTS | {"LIGHT"}


def uses_pointiness(node_tree):
    # Check if a pointiness node exists, better check would be if the node is linked
    return utils_node.has_nodes(node_tree, "LuxCoreNodeTexPointiness", True)


def get_material(obj, material_index, exporter, depsgraph, is_viewport_render):
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
        lux_mat_name, mat_props = material.convert(exporter, depsgraph, mat, is_viewport_render, obj.name)
        node_tree = mat.luxcore.node_tree
        return lux_mat_name, mat_props, node_tree
    else:
        lux_mat_name, mat_props = material.fallback()
        return lux_mat_name, mat_props, None


def _update_stats(engine, current_obj_name, extra_obj_info, current_index, total_object_count):
    engine.update_stats("Export", f"Object: {current_obj_name}{extra_obj_info} ({current_index}/{total_object_count})")
    engine.update_progress(current_index / total_object_count)


def get_obj_count_estimate(depsgraph):
    # This is faster than len(depsgraph.object_instances)
    # TODO: count dupliverts and dupliframes
    obj_count = len(depsgraph.ids)
    for id in depsgraph.ids:
        try:
            for psys in id.particle_systems:
                settings = psys.settings
                particle_count = settings.count
                if settings.child_type != "NONE":
                    particle_count *= settings.rendered_child_count
                obj_count += particle_count
        except AttributeError:
            pass
    return obj_count


class Duplis:
    def __init__(self, exported_obj):
        self.exported_obj = exported_obj
        self.matrices = array("f", [])
        self.object_ids = array("I", [])

    def get_count(self):
        return len(self.object_ids)


class ObjectCache2:
    def __init__(self):
        self.exported_objects = {}
        self.exported_meshes = {}

    def first_run(self, exporter, depsgraph, view_layer, engine, luxcore_scene, scene_props, is_viewport_render):
        instances = {}

        if engine:
            obj_count_estimate = max(1, get_obj_count_estimate(depsgraph))

        for index, dg_obj_instance in enumerate(depsgraph.object_instances):
            obj = dg_obj_instance.object

            if dg_obj_instance.is_instance and obj.type in MESH_OBJECTS:
                if engine and index % 5000 == 0:
                    if engine.test_break():
                        return False
                    _update_stats(engine, obj.name, " (dupli)", index, obj_count_estimate)

                try:
                    # The code in this try block is performance-critical, as it is
                    # executed most often when exporting millions of instances.
                    duplis = instances[obj]
                    # If duplis is None, then a non-exportable object like a curve with zero faces is being duplicated
                    if duplis:
                        obj_id = dg_obj_instance.object.original.luxcore.id
                        if obj_id == -1:
                            obj_id = dg_obj_instance.random_id & 0xfffffffe
                        duplis.object_ids.append(obj_id)
                        # We need a copy of matrix_world here, not sure why, but if we don't
                        # make a copy, we only get an identity matrix in C++
                        duplis.matrices.extend(pyluxcore.BlenderMatrix4x4ToList(dg_obj_instance.matrix_world.copy()))
                except KeyError:
                    if engine:
                        if engine.test_break():
                            return False
                        _update_stats(engine, obj.name, " (dupli)", index, obj_count_estimate)

                    exported_obj = self._convert_obj(exporter, dg_obj_instance, obj, depsgraph,
                                                     luxcore_scene, scene_props, is_viewport_render,
                                                     keep_track_of=False, engine=engine)

                    if exported_obj:
                        # Note, the transformation matrix and object ID of this first instance is not added
                        # to the duplication list, since it already exists in the scene
                        instances[obj] = Duplis(exported_obj)
                    else:
                        # Could not export the object, happens e.g. with curve objects with zero faces
                        instances[obj] = None
            else:
                # It's a regular object, not a dupli
                if not (self._is_visible(dg_obj_instance, obj) or obj.visible_get(view_layer=view_layer)):
                    continue

                if engine:
                    if engine.test_break():
                        return False
                    _update_stats(engine, obj.name, "", index, obj_count_estimate)

                self._convert_obj(exporter, dg_obj_instance, obj, depsgraph, luxcore_scene,
                                  scene_props, is_viewport_render, engine=engine)

        # Need to parse so we have the dupli objects available for DuplicateObject
        luxcore_scene.Parse(scene_props)

        for obj, duplis in instances.items():
            if duplis is None:
                # If duplis is None, then a non-exportable object like a curve with zero faces is being duplicated
                continue

            if duplis.get_count() == 1:
                # Nothing to do regarding duplication, just track the object
                # TODO check if we can modify key generation so that we only create
                #  keys from objects, not dg_obj_instance
                # obj_key = utils.make_key_from_instance(dg_obj_instance)
                # self.exported_objects[obj_key] = duplis.exported_obj
                continue

            print("obj", obj.name, "has", duplis.get_count(), "instances")

            for part in duplis.exported_obj.parts:
                src_name = part.lux_obj
                dst_name = src_name + "dupli"
                luxcore_scene.DuplicateObject(src_name, dst_name, duplis.get_count(), duplis.matrices, duplis.object_ids)

                # TODO: support steps and times (motion blur)
                # steps = 0 # TODO
                # times = array("f", [])
                # luxcore_scene.DuplicateObject(src_name, dst_name, count, steps, times, transformations)

        #self._debug_info()
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
        return dg_obj_instance.show_self and self._is_obj_visible(obj)

    def _is_obj_visible(self, obj):
        return not obj.luxcore.exclude_from_render and obj.type in EXPORTABLE_OBJECTS

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

    def _convert_obj(self, exporter, dg_obj_instance, obj, depsgraph, luxcore_scene,
                     scene_props, is_viewport_render, keep_track_of=True, engine=None):
        """ Convert one DepsgraphObjectInstance amd optionally keep track of it with self.exported_objects """
        if obj.type == "EMPTY" or obj.data is None:
            return

        obj_key = utils.make_key_from_instance(dg_obj_instance)
        exported_stuff = None
        props = pyluxcore.Properties()

        if obj.type in MESH_OBJECTS:
            # assert obj_key not in self.exported_objects
            exported_stuff = self._convert_mesh_obj(exporter, dg_obj_instance, obj, obj_key, depsgraph,
                                                    luxcore_scene, scene_props, is_viewport_render)
            if exported_stuff:
                props = exported_stuff.get_props()
        elif obj.type == "LIGHT":
            props, exported_stuff = light.convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene,
                                                        dg_obj_instance.matrix_world.copy(), is_viewport_render)

        if exported_stuff:
            scene_props.Set(props)
            if keep_track_of:
                self.exported_objects[obj_key] = exported_stuff

        # Convert hair
        for psys in obj.particle_systems:
            settings = psys.settings

            if settings.type == "HAIR" and settings.render_type == "PATH":
                lux_obj, lux_mat = convert_hair(exporter, obj, obj_key, psys, depsgraph, luxcore_scene,
                                                is_viewport_render, dg_obj_instance.is_instance,
                                                dg_obj_instance.matrix_world, engine)

                # TODO handle case when exported_stuff is None
                if exported_stuff:
                    # Should always be the case because lights can't have particle systems
                    assert isinstance(exported_stuff, ExportedObject)
                    # Hair export uses same name for object and shape
                    exported_stuff.parts.append(ExportedPart(lux_obj, lux_obj, lux_mat))

        return exported_stuff

    def _convert_mesh_obj(self, exporter, dg_obj_instance, obj, obj_key, depsgraph,
                          luxcore_scene, scene_props, is_viewport_render):
        transform = dg_obj_instance.matrix_world

        use_instancing = is_viewport_render or dg_obj_instance.is_instance or utils.can_share_mesh(obj.original) \
                         or (exporter.motion_blur_enabled and obj.luxcore.enable_motion_blur)

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
                shape = shape_name
                lux_mat_name, mat_props, node_tree = get_material(obj, mat_index, exporter, depsgraph, is_viewport_render)
                scene_props.Set(mat_props)
                mat_names.append(lux_mat_name)

                if node_tree:
                    warn_about_missing_uvs(obj, node_tree)

                    output_node = get_active_output(node_tree)
                    if output_node:
                        try:
                            # Convert the whole shape stack
                            # TODO support for instances
                            shape = output_node.inputs["Shape"].export_shape(exporter, depsgraph, scene_props, shape)
                        except KeyError:
                            # TODO remove this try/except, instead add the socket in utils/compatibility.py
                            pass

                    if uses_pointiness(node_tree):
                        # Replace shape definition with pointiness shape
                        pointiness_shape = shape + "_pointiness"
                        prefix = "scene.shapes." + pointiness_shape + "."
                        scene_props.Set(pyluxcore.Property(prefix + "type", "pointiness"))
                        scene_props.Set(pyluxcore.Property(prefix + "source", shape))
                        shape = pointiness_shape

                exported_mesh.mesh_definitions[idx] = [shape, mat_index]

            obj_transform = transform.copy() if use_instancing else None
            obj_id = utils.make_object_id(dg_obj_instance)

            return ExportedObject(obj_key, exported_mesh.mesh_definitions, mat_names,
                                  obj_transform, obj.luxcore.visible_to_camera, obj_id)


    def diff(self, depsgraph):
        only_scene = len(depsgraph.updates) == 1 and isinstance(depsgraph.updates[0].id, bpy.types.Scene)
        return depsgraph.id_type_updated("OBJECT") and not only_scene

    def update(self, exporter, depsgraph, luxcore_scene, scene_props, is_viewport_render=True):
        redefine_objs_with_these_mesh_keys = []
        # Always instance in viewport so we can move objects around
        use_instancing = True

        # Geometry updates (mesh edit, modifier edit etc.)
        if depsgraph.id_type_updated("OBJECT"):
            for dg_update in depsgraph.updates:
                if dg_update.is_updated_geometry and isinstance(dg_update.id, bpy.types.Object):
                    obj = dg_update.id
                    if not self._is_obj_visible(obj):
                        continue

                    obj_key = utils.make_key(obj)

                    if obj.type in MESH_OBJECTS:
                        mesh_key = self._get_mesh_key(obj, use_instancing)

                        # if mesh_key not in self.exported_meshes:
                        # TODO this can happen if a deforming modifier is added
                        #  to an already-exported object. how to handle this case?

                        transform = None  # In viewport render, everything is instanced
                        exported_mesh = mesh_converter.convert(obj, mesh_key, depsgraph, luxcore_scene,
                                                               is_viewport_render, use_instancing, transform)
                        self.exported_meshes[mesh_key] = exported_mesh

                        # We arrive here not only when the mesh is edited, but also when the material
                        # of the object is changed in Blender. In this case we have to re-define all
                        # objects using this mesh (just the properties, the mesh is not re-exported).
                        redefine_objs_with_these_mesh_keys.append(mesh_key)
                    elif obj.type == "LIGHT":
                        print(f"Light obj {obj.name} was updated")
                        props, exported_stuff = light.convert_light(exporter, obj, obj_key, depsgraph, luxcore_scene,
                                                                    obj.matrix_world.copy(), is_viewport_render)
                        if exported_stuff:
                            self.exported_objects[obj_key] = exported_stuff
                            scene_props.Set(props)

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
            mesh_key = self._get_mesh_key(obj, use_instancing)

            if (obj_key in self.exported_objects and obj.type != "LIGHT") and not mesh_key in redefine_objs_with_these_mesh_keys:
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

        #self._debug_info()
