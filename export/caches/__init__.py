from ... import utils
from .. import camera

from .object_cache import ObjectCache2

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
