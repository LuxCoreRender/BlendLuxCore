import bpy
from .. import utils
from ..utils import node as utils_node
from ..export import camera


class StringCache(object):
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


class CameraCache(object):
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
        if scene.camera and (scene.camera.is_updated or scene.camera.is_updated_data):
            return True

        return has_changes


class ObjectCache(object):
    def __init__(self):
        self._reset()

    def get_changed_transform(self):
        # Return as a set to eliminate duplicates
        return set(self.changed_transform)

    def get_changed_mesh(self):
        return set(self.changed_mesh)

    def get_changed_lamps(self):
        return set(self.changed_lamps)

    def _reset(self):
        self.changed_transform = []
        self.changed_mesh = []
        self.changed_lamps = []

    def _check(self, obj):
        if obj.is_updated_data:
            if obj.type in ["MESH", "CURVE", "SURFACE", "META", "FONT"]:
                self.changed_mesh.append(obj)
            elif obj.type in ["LAMP"]:
                self.changed_lamps.append(obj)

        if obj.is_updated:
            if obj.type in ["MESH", "CURVE", "SURFACE", "META", "FONT", "EMPTY"]:
                # check if a new material was assigned
                if obj.data and obj.data.is_updated:
                    self.changed_mesh.append(obj)
                else:
                    self.changed_transform.append(obj)
            elif obj.type == "LAMP":
                self.changed_lamps.append(obj)

        return obj.is_updated_data or obj.is_updated

    def diff(self, scene):
        self._reset()

        if bpy.data.objects.is_updated:
            for obj in scene.objects:
                self._check(obj)

                if obj.dupli_group:
                    # It is an empty used to instance a group
                    child_obj_changed = False

                    for child_obj in obj.dupli_group.objects:
                        child_obj_changed |= self._check(child_obj)

                    if child_obj_changed:
                        # Flag the duplicator object (empty) for update
                        self.changed_mesh.append(obj)

        return self.changed_transform or self.changed_mesh or self.changed_lamps


class MaterialCache(object):
    def __init__(self):
        self._reset()

    def _reset(self):
        self.changed_materials = []

    def diff(self):
        self._reset()

        if bpy.data.materials.is_updated:
            for mat in bpy.data.materials:
                node_tree = mat.luxcore.node_tree
                mat_updated = False

                if mat.is_updated:
                    mat_updated = True
                elif node_tree:
                    if node_tree.is_updated or node_tree.is_updated_data:
                        mat_updated = True

                    # Check pointer nodes for changes
                    pointer_nodes = utils_node.find_nodes(node_tree, "LuxCoreNodeTreePointer")
                    for node in pointer_nodes:
                        pointer_tree = node.node_tree
                        if pointer_tree and (pointer_tree.is_updated or pointer_tree.is_updated_data):
                            mat_updated = True

                if mat_updated:
                    self.changed_materials.append(mat)

        return self.changed_materials


class VisibilityCache(object):
    def __init__(self):
        # sets containing keys
        self.last_visible_objects = None
        self.objects_to_remove = None
        self.objects_to_add = None

    def diff(self, context):
        visible_objs = self._get_visible_objects(context)
        if self.last_visible_objects is None:
            # Not initialized yet
            self.last_visible_objects = visible_objs
            return False

        self.objects_to_remove = self.last_visible_objects - visible_objs
        self.objects_to_add = visible_objs - self.last_visible_objects
        self.last_visible_objects = visible_objs
        return self.objects_to_remove or self.objects_to_add

    def _get_visible_objects(self, context):
        as_keylist = [utils.make_key(obj) for obj in context.visible_objects]
        return set(as_keylist)


class WorldCache(object):
    def __init__(self):
        self.world_name = None

    def diff(self, context):
        world = context.scene.world
        world_updated = False

        if world:
            world_updated = world.is_updated or world.is_updated_data or self.world_name != world.name

            # The sun influcences the world, e.g. through direction and turbidity if sky2 is used
            sun = world.luxcore.sun
            if sun:
                world_updated |= sun.is_updated or sun.is_updated_data or (sun.data and sun.data.is_updated)
        elif self.world_name:
            # We had a world, but it was deleted
            world_updated = True

        self.world_name = world.name if world else None
        return world_updated
