import bpy
from ... import utils
from .. import camera, material
from .object_cache import EXPORTABLE_OBJECTS

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
        self.changed_materials = set()

    def diff(self, depsgraph):
        if depsgraph.id_type_updated("MATERIAL"):
            for dg_update in depsgraph.updates:
                if isinstance(dg_update.id, bpy.types.Material):
                    self.changed_materials.add(dg_update.id)
                    print("mat update:", dg_update.id.name)
        return self.changed_materials

    def update(self, exporter, depsgraph, is_viewport_render, props):
        for mat in self.changed_materials:
            lux_mat_name, mat_props = material.convert(exporter, depsgraph, mat, is_viewport_render)
            props.Set(mat_props)
        self.changed_materials.clear()

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

    def diff(self, depsgraph):
        visible_objs = self._get_visible_objects(depsgraph)
        if self.last_visible_objects is None:
            # Not initialized yet
            self.last_visible_objects = visible_objs
            return False

        self.objects_to_remove = self.last_visible_objects - visible_objs
        self.last_visible_objects = visible_objs
        return self.objects_to_remove

    def _get_visible_objects(self, depsgraph):
        keys = set()
        for dg_obj_instance in depsgraph.object_instances:
            if dg_obj_instance.show_self:
                obj = dg_obj_instance.instance_object if dg_obj_instance.is_instance else dg_obj_instance.object
                if obj.type in EXPORTABLE_OBJECTS:
                    keys.add(utils.make_key_from_instance(dg_obj_instance))
        return keys


class WorldCache:
    def __init__(self):
        self.world_name = None

    def diff(self, depsgraph):
        world = depsgraph.scene_eval.world
        world_updated = False

        if world:
            # TODO 2.8 for some reason this fires when editing a node tree, even when the world is not touched at all
            world_updated = depsgraph.id_type_updated("WORLD") or self.world_name != world.name_full

            # The sun influcences the world, e.g. through direction and turbidity if sky2 is used
            if world.luxcore.light == "sky2" and depsgraph.id_type_updated("OBJECT"):
                for dg_update in depsgraph.updates:
                    if dg_update.id == world.luxcore.sun:
                        world_updated = True
                        break
        elif self.world_name:
            # We had a world, but it was deleted
            world_updated = True

        self.world_name = world.name_full if world else None
        return world_updated
