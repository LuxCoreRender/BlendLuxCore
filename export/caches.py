import bpy
from .. import utils
from ..utils import node as utils_node
from ..export import blender_object, camera, blender_object_280


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
        self.last_instance_transforms = {}

    def first_run(self, depsgraph, engine, luxcore_scene, scene_props, is_viewport_render):
        # for debug
        used_names = set()

        for index, dg_obj_instance in enumerate(depsgraph.object_instances, start=1):
            if not dg_obj_instance.show_self:
                continue

            obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
            if obj.type not in blender_object_280.EXPORTABLE_OBJECTS:
                continue

            transform = dg_obj_instance.matrix_world
            # print(f"obj {obj}, is_instance: {dg_obj_instance.is_instance}, transform: {transform}")
            use_instancing = True
            key = utils.make_key_from_instance(dg_obj_instance)
            luxcore_name_base = utils.make_name_from_instance(dg_obj_instance)
            exported_obj = blender_object_280.convert(obj, luxcore_name_base, depsgraph, luxcore_scene, is_viewport_render, use_instancing, transform)
            if exported_obj:
                scene_props.Set(exported_obj.get_props())
                self.exported_objects[key] = exported_obj

            if engine:
                # Objects are the most expensive to export, so they dictate the progress
                # engine.update_progress(index / obj_amount)
                if engine.test_break():
                    return False

            if luxcore_name_base in used_names:
                print("WARNING: NAME ALREADY USED!", luxcore_name_base, obj.name)
                print("parent:", dg_obj_instance.parent)
                print("is_instance:", dg_obj_instance.is_instance)
            used_names.add(luxcore_name_base)
        return True

    def diff(self, depsgraph):
        return depsgraph.id_type_updated("OBJECT")

    def update(self, depsgraph, scene_props):
        print("object cache update")

        # For now, transforms only
        for dg_obj_instance in depsgraph.object_instances:
            if not dg_obj_instance.show_self:
                continue

            key = utils.make_key_from_instance(dg_obj_instance)
            transform = dg_obj_instance.matrix_world.copy()
            try:
                exported_obj = self.exported_objects[key]
                last_transform = exported_obj.transform
                if last_transform != transform:
                    print("instance needs transform update:", dg_obj_instance)
                    # Update transform
                    exported_obj.transform = transform
                    scene_props.Set(exported_obj.get_props())
            except KeyError:
                print("Instance not yet exported")
                # Do export
                ...


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
