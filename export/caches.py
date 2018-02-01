import bpy
from .. import utils
from ..utils import node as utils_node
from ..nodes.output import get_active_output
from ..export import smoke

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


class ObjectCache(object):
    def __init__(self):
        self._reset()

    def _reset(self):
        self.changed_transform = []
        self.changed_mesh = []
        self.lamps = []

    def diff(self, scene):
        self._reset()

        if bpy.data.objects.is_updated:
            for obj in scene.objects:
                if obj.is_updated_data:
                    if obj.type in ["MESH", "CURVE", "SURFACE", "META", "FONT"]:
                        self.changed_mesh.append(obj)
                    elif obj.type in ["LAMP"]:
                        self.lamps.append(obj)

                if obj.is_updated:
                    if obj.type in ["MESH", "CURVE", "SURFACE", "META", "FONT", "EMPTY"]:
                        # check if a new material was assigned
                        if obj.data and obj.data.is_updated:
                            self.changed_mesh.append(obj)
                        else:
                            self.changed_transform.append(obj)
                    elif obj.type == "LAMP":
                        self.lamps.append(obj)

        return self.changed_transform or self.changed_mesh or self.lamps


class MaterialCache(object):
    def __init__(self):
        self._reset()

    def _reset(self):
        self.changed_materials = []

    def diff(self):
        if bpy.data.materials.is_updated:
            for mat in bpy.data.materials:
                node_tree = mat.luxcore.node_tree
                mat_updated = False

                if mat.is_updated:
                    mat_updated = True
                elif node_tree:
                    if node_tree.is_updated or node_tree.is_updated_data:
                        mat_updated = True

                    # Check linked volumes for changes
                    active_output = get_active_output(node_tree)
                    interior_vol = utils_node.get_linked_node(active_output.inputs["Interior Volume"])
                    if interior_vol and (interior_vol.is_updated or interior_vol.is_updated_data):
                        mat_updated = True
                    exterior_vol = utils_node.get_linked_node(active_output.inputs["Exterior Volume"])
                    if exterior_vol and (exterior_vol.is_updated or exterior_vol.is_updated_data):
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


class SmokeCache(object):
    """
    Only speeds up viewport updates that are not related to volume updates (e.g. when a material in the scene is edited,
    this cache prevents that smoke is re-exported and pyluxcore.Properties are set just to check for volume updates.
    The really expensive operation is *not* the smoke export, but the Property setting.)
    """    
    def __init__(self):
        cache = {}
    
    def convert(self, smoke_obj, channel):
        key = utils.get_luxcore_name(smoke_obj, context) + channel

        if key not in cls.cache:
            self.cache[key] = smoke.convert(smoke_obj, channel)

        return self.cache[key]

    def reset(self):
        self.cache = {}



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
    def diff(self, context):
        world = context.scene.world
        if world:
            world_updated = world.is_updated or world.is_updated_data

            # The sun influcences the world, e.g. through direction and turbidity if sky2 is used
            sun = world.luxcore.sun
            if sun:
                sun_updated = sun.is_updated or sun.is_updated_data or (sun.data and sun.data.is_updated)
            else:
                sun_updated = False

            return world_updated or sun_updated
        return False
