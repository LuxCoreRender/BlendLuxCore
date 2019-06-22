import bpy
from .. import utils
from ..utils import node as utils_node
from ..export import blender_object, camera
from .blender_object_280 import ExportedObject, ExportedMesh, ExportedLight, EXPORTABLE_OBJECTS, MESH_OBJECTS


class StringCache:
    def __init__(self):
        self.props = None

    def diff(self, new_props):
        props_str = str(self.props)
        new_props_str = str(new_props)

        if self.props is None:
            # Not initialized yet
            self.props = new_props
            return True

        has_changes = props_str != new_props_str
        self.props = new_props
        return has_changes


class CameraCache:
    def __init__(self):
        self.string_cache = StringCache()

    @property
    def props(self):
        return self.string_cache.props

    def diff(self, exporter, scene, context):
        # String cache
        camera_props = camera.convert(exporter, scene, context)
        has_changes = self.string_cache.diff(camera_props)

        # Check camera object and data for changes
        # Needed in case the volume node tree was relinked/unlinked
        # TODO 2.8
        # if scene.camera and (scene.camera.is_updated or scene.camera.is_updated_data):
        #     return True

        return has_changes


class ObjectCache2:
    def __init__(self):
        pass
        self.exported_objects = {}
        self.exported_meshes = {}

    def first_run(self, depsgraph, engine, luxcore_scene, scene_props, is_viewport_render):
        for index, dg_obj_instance in enumerate(depsgraph.object_instances, start=1):
            obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
            if not self._is_visible(dg_obj_instance, obj):
                continue

            self._convert(dg_obj_instance, obj, depsgraph, luxcore_scene, scene_props, is_viewport_render)
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
            print(key, exported_mesh.mesh_definitions)

    def _is_visible(self, dg_obj_instance, obj):
        if not dg_obj_instance.show_self:
            return False
        if obj.type not in EXPORTABLE_OBJECTS:
            return False
        return True

    def _convert(self, dg_obj_instance, obj, depsgraph, luxcore_scene, scene_props, is_viewport_render):
        """ Convert one DepsgraphObjectInstance amd keep track of it """
        obj_key = utils.make_key_from_instance(dg_obj_instance)
        if obj_key in self.exported_objects:
            raise Exception("key already in exp_obj:", obj_key)

        if obj.type == "EMPTY" or obj.data is None:
            # Not sure if we even need a special empty export, could just ignore them
            print("empty export not implemented yet")
        elif obj.type in MESH_OBJECTS:
            print("converting mesh object", obj.name_full)
            self._convert_mesh_obj(dg_obj_instance, obj, obj_key, depsgraph, luxcore_scene, scene_props, is_viewport_render)
        elif obj.type == "LIGHT":
            print("light export not implemented yet")
            transform = dg_obj_instance.matrix_world.copy()
            return ExportedLight(obj_key, transform)

    def _convert_mesh_obj(self, dg_obj_instance, obj, obj_key, depsgraph, luxcore_scene, scene_props, is_viewport_render):
        transform = dg_obj_instance.matrix_world

        use_instancing = is_viewport_render or dg_obj_instance.is_instance or utils.can_share_mesh(obj)
        mesh_key = utils.get_luxcore_name(obj.data, is_viewport_render)

        if use_instancing and mesh_key in self.exported_meshes:
            print("retrieving mesh from cache")
            exported_mesh = self.exported_meshes[mesh_key]
        else:
            print("fresh export")
            from . import mesh_converter
            exported_mesh = mesh_converter.convert(obj, mesh_key, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform)
            self.exported_meshes[mesh_key] = exported_mesh

        obj_transform = transform if use_instancing else None
        exported_obj = ExportedObject(obj_key, exported_mesh.mesh_definitions, obj_transform)
        if exported_obj:
            scene_props.Set(exported_obj.get_props())
            self.exported_objects[obj_key] = exported_obj

    def diff(self, depsgraph):
        return depsgraph.id_type_updated("OBJECT")

    def update(self, depsgraph, luxcore_scene, scene_props, is_viewport_render=True):
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

            key = utils.make_key_from_instance(dg_obj_instance)
            transform = dg_obj_instance.matrix_world.copy()
            try:
                exported_obj = self.exported_objects[key]
                last_transform = exported_obj.transform
                if last_transform != transform:
                    # Update transform
                    exported_obj.transform = transform
                    scene_props.Set(exported_obj.get_props())
            except KeyError:
                # Do export
                self._convert(dg_obj_instance, obj, depsgraph, luxcore_scene, scene_props, is_viewport_render)

        # TODO: mesh updates

        self._debug_info()


class ObjectCache:
    class ChangeType:
        # Types of object changes
        NONE = 0
        TRANSFORM = 1 << 0
        MESH = 1 << 1
        LIGHT = 1 << 2

    def __init__(self):
        self._reset()

    def _reset(self):
        # We use sets to make duplicates impossible
        self.changed_transform = set()
        self.changed_mesh = set()
        self.changed_lights = set()

    def _check(self, obj):
        changes = self.ChangeType.NONE

        if obj.is_updated_data:
            if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}:
                self.changed_mesh.add(obj)
                changes |= self.ChangeType.MESH
            elif obj.type == "LIGHT":
                self.changed_lights.add(obj)
                changes |= self.ChangeType.LIGHT

        if obj.is_updated:
            if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT", "EMPTY"}:
                # check if a new material was assigned
                if obj.data and obj.data.is_updated:
                    self.changed_mesh.add(obj)
                    changes |= self.ChangeType.MESH
                else:
                    self.changed_transform.add(obj)
                    changes |= self.ChangeType.TRANSFORM
            elif obj.type == "LIGHT":
                self.changed_lights.add(obj)
                changes |= self.ChangeType.LIGHT

        return changes

    def _check_group(self, duplicator_obj, dupli_group):
        child_obj_changes = self.ChangeType.NONE

        for child_obj in dupli_group.objects:
            child_obj_changes |= self._check(child_obj)

        if child_obj_changes & (self.ChangeType.MESH | self.ChangeType.LIGHT):
            # Flag the duplicator object for update
            self.changed_mesh.add(duplicator_obj)

        return child_obj_changes

    def diff(self, scene, ignored_objs=None):
        self._reset()

        if bpy.data.objects.is_updated:
            for obj in scene.objects:
                # Skip the object if it was touched by our previous export, for
                # example because tessfaces for the mesh were generated.
                # This prevents unnecessary updates when starting the viewport render.
                if ignored_objs and obj in ignored_objs:
                    continue

                self._check(obj)

                if obj.dupli_group:
                    # It is an empty used to instance a group
                    self._check_group(obj, obj.dupli_group)

                for particle_system in obj.particle_systems:
                    settings = particle_system.settings

                    if settings.render_type == "OBJECT":
                        changes = self._check(settings.dupli_object)
                        if changes & (self.ChangeType.MESH | self.ChangeType.LIGHT):
                            # The data of the source object was modified,
                            # flag the duplicator for update
                            self.changed_mesh.add(obj)
                    elif settings.render_type == "GROUP":
                        self._check_group(obj, settings.dupli_group)

        return self.changed_transform or self.changed_mesh or self.changed_lights


class MaterialCache:
    def __init__(self):
        self._reset()

    def _reset(self):
        self.changed_materials = set()

    def diff(self, depsgraph):
        # TODO
        return depsgraph.id_type_updated("MATERIAL")

    def update(self, depsgraph, props):
        print("mat cache update todo")

# def diff(self, ignored_mats=None):
    #     self._reset()
    #
    #     if bpy.data.materials.is_updated:
    #         for mat in bpy.data.materials:
    #             if ignored_mats and mat in ignored_mats:
    #                 continue
    #
    #             node_tree = mat.luxcore.node_tree
    #             mat_updated = False
    #
    #             if mat.is_updated:
    #                 mat_updated = True
    #             elif node_tree:
    #                 if node_tree.is_updated or node_tree.is_updated_data:
    #                     mat_updated = True
    #
    #                 # Check pointer nodes for changes
    #                 pointer_nodes = utils_node.find_nodes(node_tree, "LuxCoreNodeTreePointer")
    #                 for node in pointer_nodes:
    #                     pointer_tree = node.node_tree
    #                     if pointer_tree and (pointer_tree.is_updated or pointer_tree.is_updated_data):
    #                         mat_updated = True
    #
    #             if mat_updated:
    #                 self.changed_materials.add(mat)
    #
    #     return self.changed_materials


class VisibilityCache:
    def __init__(self):
        # sets containing keys
        self.last_visible_objects = None
        self.objects_to_remove = None
        self.objects_to_add = None

    def diff(self, depsgraph):
        visible_objs = self._get_visible_objects(depsgraph)
        if self.last_visible_objects is None:
            # Not initialized yet
            self.last_visible_objects = visible_objs
            return False

        self.objects_to_remove = self.last_visible_objects - visible_objs
        self.objects_to_add = visible_objs - self.last_visible_objects
        self.last_visible_objects = visible_objs
        return self.objects_to_remove or self.objects_to_add

    def _get_visible_objects(self, depsgraph):
        # as_keylist = [utils.make_key(obj) for obj in context.visible_objects
        #               if obj.type in blender_object.EXPORTABLE_OBJECTS]
        # TODO check if we can actually use dgobjinst.instance_object for non-instances
        as_keylist = [utils.make_key_from_instance(dg_obj_instance) for dg_obj_instance in depsgraph.object_instances
                      if dg_obj_instance.show_self and dg_obj_instance.instance_object]
        return set(as_keylist)


class WorldCache:
    def __init__(self):
        self.world_name = None

    def diff(self, depsgraph):
        world = depsgraph.scene_eval.world
        world_updated = False

        if world:
            # TODO 2.8 remove commented
            # world_updated = world.is_updated or world.is_updated_data or self.world_name != world.name
            world_updated = depsgraph.id_type_updated("WORLD") or self.world_name != world.name

            # The sun influcences the world, e.g. through direction and turbidity if sky2 is used
            # TODO 2.8
            # sun = world.luxcore.sun
            # if sun:
            #     world_updated |= sun.is_updated or sun.is_updated_data or (sun.data and sun.data.is_updated)
        elif self.world_name:
            # We had a world, but it was deleted
            world_updated = True

        self.world_name = world.name_full if world else None
        return world_updated
