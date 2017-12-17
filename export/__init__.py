import bpy
from ..bin import pyluxcore
from .. import utils
from . import blender_object, camera, config, light, material
from .light import WORLD_BACKGROUND_LIGHT_NAME


class Change:
    NONE = 0

    CONFIG = 1 << 0
    CAMERA = 1 << 1
    OBJECT = 1 << 2
    MATERIAL = 1 << 3
    VISIBILITY = 1 << 4
    WORLD = 1 << 5

    REQUIRES_SCENE_EDIT = CAMERA | OBJECT | MATERIAL | VISIBILITY | WORLD
    REQUIRES_VIEW_UPDATE = CONFIG


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
        self.node_cache = StringCache()

    def diff(self):
        if bpy.data.materials.is_updated:
            for mat in bpy.data.materials:
                node_tree = mat.luxcore.node_tree
                mat_updated = False

                if node_tree and (node_tree.is_updated or node_tree.is_updated_data):
                    luxcore_name, props = material.convert(mat)
                    if self.node_cache.diff(props):
                        mat_updated = True
                else:
                    mat_updated = mat.is_updated

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


class Exporter(object):
    def __init__(self):
        print("exporter init")
        self.config_cache = StringCache()
        self.camera_cache = StringCache()
        self.object_cache = ObjectCache()
        self.material_cache = MaterialCache()
        self.visibility_cache = VisibilityCache()
        self.world_cache = WorldCache()
        # This dict contains ExportedObject and ExportedLight instances
        self.exported_objects = {}

    def create_session(self, scene, context=None):
        print("create_session")
        # Scene
        luxcore_scene = pyluxcore.Scene()
        scene_props = pyluxcore.Properties()

        # Camera (needs to be parsed first because it is needed for hair tesselation)
        camera_props = camera.convert(scene, context)
        self.camera_cache.diff(camera_props)  # Init camera cache
        luxcore_scene.Parse(camera_props)

        # Objects and lamps
        objs = context.visible_objects if context else bpy.data.objects

        for obj in objs:
            if obj.type in ("MESH", "CURVE", "SURFACE", "META", "FONT", "LAMP"):
                props, exported_thing = blender_object.convert(obj, scene, context, luxcore_scene)
                scene_props.Set(props)
                self.exported_objects[utils.make_key(obj)] = exported_thing

        # World
        if scene.world and scene.world.luxcore.light != "none":
            props = light.convert_world(scene.world, scene)
            scene_props.Set(props)

        luxcore_scene.Parse(scene_props)

        # Config
        config_props = config.convert(scene, context)
        self.config_cache.diff(config_props)  # Init config cache
        renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)

        # Session
        return pyluxcore.RenderSession(renderconfig)

    def get_changes(self, context):
        changes = Change.NONE

        config_props = config.convert(context.scene, context)
        if self.config_cache.diff(config_props):
            changes |= Change.CONFIG

        camera_props = camera.convert(context.scene, context)
        if self.camera_cache.diff(camera_props):
            changes |= Change.CAMERA

        if self.object_cache.diff(context.scene):
            changes |= Change.OBJECT

        if self.material_cache.diff():
            changes |= Change.MATERIAL

        if self.visibility_cache.diff(context):
            changes |= Change.VISIBILITY

        if self.world_cache.diff(context):
            changes |= Change.WORLD

        return changes

    def update(self, context, session, changes):
        if changes & Change.CONFIG:
            # We already converted the new config settings during get_changes(), re-use them
            session = self._update_config(session, self.config_cache.props)

        if changes & Change.REQUIRES_SCENE_EDIT:
            luxcore_scene = session.GetRenderConfig().GetScene()
            session.BeginSceneEdit()

            try:
                props = self._scene_edit(context, changes, luxcore_scene)
                luxcore_scene.Parse(props)
            except Exception as error:
                print("Error in update():", error)
                import traceback
                traceback.print_exc()
            finally:
                session.EndSceneEdit()

        # We have to return and re-assign the session in the RenderEngine,
        # because it might have been replaced in _update_config()
        return session

    def _update_config(self, session, config_props):
        renderconfig = session.GetRenderConfig()
        session.Stop()
        del session

        renderconfig.Parse(config_props)
        if renderconfig is None:
            print("ERROR: not a valid luxcore config")
            return
        session = pyluxcore.RenderSession(renderconfig)
        session.Start()
        return session

    def _scene_edit(self, context, changes, luxcore_scene):
        props = pyluxcore.Properties()

        if changes & Change.CAMERA:
            # We already converted the new camera settings during get_changes(), re-use them
            props.Set(self.camera_cache.props)

        if changes & Change.OBJECT:
            for obj in self.object_cache.changed_transform:
                # TODO only update transform
                print("transformed:", obj.name)
                obj_props, exported_obj = blender_object.convert(obj, context.scene, context, luxcore_scene)
                props.Set(obj_props)
                self.exported_objects[utils.make_key(obj)] = exported_obj

            for obj in self.object_cache.changed_mesh:
                print("mesh changed:", obj.name)
                obj_props, exported_obj = blender_object.convert(obj, context.scene, context, luxcore_scene)
                props.Set(obj_props)
                self.exported_objects[utils.make_key(obj)] = exported_obj

            for obj in self.object_cache.lamps:
                print("lamp changed:", obj.name)
                light_props, exported_light = blender_object.convert(obj, context.scene, context, luxcore_scene)
                props.Set(light_props)
                self.exported_objects[utils.make_key(obj)] = exported_light

        if changes & Change.MATERIAL:
            for mat in self.material_cache.changed_materials:
                luxcore_name, mat_props = material.convert(mat)
                props.Set(mat_props)

        if changes & Change.VISIBILITY:
            for key in self.visibility_cache.objects_to_remove:
                if key not in self.exported_objects:
                    print('WARNING: Can not delete key "%s" from luxcore_scene' % key)
                    print("The object was probably renamed")
                    continue

                exported_thing = self.exported_objects[key]

                # exported_objects contains instances of ExportedObject and ExportedLight
                if isinstance(exported_thing, blender_object.ExportedObject):
                    remove_func = luxcore_scene.DeleteObject
                else:
                    remove_func = luxcore_scene.DeleteLight

                for luxcore_name in exported_thing.luxcore_names:
                    remove_func(luxcore_name)

                del self.exported_objects[key]

            for key in self.visibility_cache.objects_to_add:
                obj = utils.obj_from_key(key, context.visible_objects)

                obj_props, exported_obj = blender_object.convert(obj, context.scene, context, luxcore_scene)
                props.Set(obj_props)
                self.exported_objects[utils.make_key(obj)] = exported_obj

        if changes & Change.WORLD:
            if context.scene.world.luxcore.light == "none":
                luxcore_scene.DeleteLight(WORLD_BACKGROUND_LIGHT_NAME)
            else:
                world_props = light.convert_world(context.scene.world, context.scene)
                props.Set(world_props)

        return props
