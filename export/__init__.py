from time import time
import bpy
from ..bin import pyluxcore
from .. import utils
from ..utils import node as utils_node
from . import blender_object, camera, config, light, material, motion_blur
from .light import WORLD_BACKGROUND_LIGHT_NAME
from ..nodes.output import get_active_output


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

    def diff(self):
        if bpy.data.materials.is_updated:
            for mat in bpy.data.materials:
                node_tree = mat.luxcore.node_tree
                mat_updated = False

                if node_tree:
                    if node_tree.is_updated or node_tree.is_updated_data:
                        mat_updated = True

                    # Check linked volumes for changes
                    active_output = get_active_output(node_tree)
                    interior_vol = active_output.interior_volume
                    if interior_vol and (interior_vol.is_updated or interior_vol.is_updated_data):
                        mat_updated = True
                    exterior_vol = active_output.exterior_volume
                    if exterior_vol and (exterior_vol.is_updated or exterior_vol.is_updated_data):
                        mat_updated = True

                    # Check pointer nodes for changes
                    pointer_nodes = utils_node.find_nodes(node_tree, "LuxCoreNodeTreePointer")
                    for node in pointer_nodes:
                        pointer_tree = node.node_tree
                        if pointer_tree and (pointer_tree.is_updated or pointer_tree.is_updated_data):
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

    def create_session(self, engine, scene, context=None):
        print("create_session")
        scene.luxcore.errorlog.clear()
        start = time()
        # Scene
        luxcore_scene = pyluxcore.Scene()
        scene_props = pyluxcore.Properties()

        # Camera (needs to be parsed first because it is needed for hair tesselation)
        camera_props = camera.convert(scene, context)
        self.camera_cache.diff(camera_props)  # Init camera cache
        luxcore_scene.Parse(camera_props)

        # Objects and lamps
        objs = context.visible_objects if context else bpy.data.objects
        len_objs = len(objs)

        for index, obj in enumerate(objs, start=1):
            if obj.type in ("MESH", "CURVE", "SURFACE", "META", "FONT", "LAMP"):
                engine.update_stats("Export", "Object: %s (%d/%d)" % (obj.name, index, len_objs))
                self._convert_object(scene_props, obj, scene, context, luxcore_scene)
                # Objects are the most expensive to export, so they dictate the progress
                engine.update_progress(index / len_objs)
            # Regularly check if we should abort the export (important in heavy scenes)
            if engine.test_break():
                return None

        # Motion blur
        if scene.camera:
            blur_settings = scene.camera.data.luxcore.motion_blur
            # Don't export camera blur in viewport
            camera_blur = blur_settings.camera_blur and not context
            enabled = blur_settings.enable and (blur_settings.object_blur or camera_blur)

            if enabled and blur_settings.shutter > 0:
                motion_blur_props = motion_blur.convert(context, scene, objs, self.exported_objects)
                if camera_blur:
                    motion_blur_props.Set(camera_props)
                scene_props.Set(motion_blur_props)

        # World
        if scene.world and scene.world.luxcore.light != "none":
            engine.update_stats("Export", "World")
            props = light.convert_world(scene.world, scene)
            scene_props.Set(props)

        luxcore_scene.Parse(scene_props)

        # Regularly check if we should abort the export (important in heavy scenes)
        if engine.test_break():
            return None

        # Convert config at last because all lightgroups and passes have to be already defined
        config_props = config.convert(scene, context)
        self.config_cache.diff(config_props)  # Init config cache
        renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)

        # Regularly check if we should abort the export (important in heavy scenes)
        if engine.test_break():
            return None

        # Session
        engine.update_stats("Export", "Creating session")
        session = pyluxcore.RenderSession(renderconfig)

        elapsed_msg = "Session created in %.1fs" % (time() - start)
        print(elapsed_msg)
        engine.update_stats("Export", elapsed_msg)

        return session

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
                context.scene.luxcore.errorlog.add_error(error)
                import traceback
                traceback.print_exc()

            try:
                session.EndSceneEdit()
            except RuntimeError as error:
                context.scene.luxcore.errorlog.add_error(error)
                # Probably no light source, save ourselves by adding one (otherwise a crash happens)
                props = pyluxcore.Properties()
                props.Set(pyluxcore.Property("scene.lights.__SAVIOR__.type", "constantinfinite"))
                props.Set(pyluxcore.Property("scene.lights.__SAVIOR__.color", [0, 0, 0]))
                luxcore_scene.Parse(props)
                # Try again
                session.EndSceneEdit()

            if session.IsInPause():
                session.Resume()

        # We have to return and re-assign the session in the RenderEngine,
        # because it might have been replaced in _update_config()
        return session

    def _convert_object(self, props, obj, scene, context, luxcore_scene, update_mesh=False):
        key = utils.make_key(obj)
        old_exported_obj = None

        if key not in self.exported_objects:
            # We have to update the mesh because the object was not yet exported
            update_mesh = True

        if not update_mesh:
            # We need the previously exported mesh defintions
            old_exported_obj = self.exported_objects[key]

        # Note: exported_obj can also be an instance of ExportedLight, but they behave the same
        obj_props, exported_obj = blender_object.convert(obj, scene, context, luxcore_scene, old_exported_obj, update_mesh)

        if exported_obj is None:
            # Object is not visible or an error happened.
            # In case of an error, it was already reported by blender_object.convert()
            return

        props.Set(obj_props)
        self.exported_objects[key] = exported_obj

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
                self._convert_object(props, obj, context.scene, context, luxcore_scene, update_mesh=False)

            for obj in self.object_cache.changed_mesh:
                print("mesh changed:", obj.name)
                self._convert_object(props, obj, context.scene, context, luxcore_scene, update_mesh=True)

            for obj in self.object_cache.lamps:
                print("lamp changed:", obj.name)
                self._convert_object(props, obj, context.scene, context, luxcore_scene)

        if changes & Change.MATERIAL:
            for mat in self.material_cache.changed_materials:
                luxcore_name, mat_props = material.convert(mat, context.scene)
                props.Set(mat_props)

        if changes & Change.VISIBILITY:
            for key in self.visibility_cache.objects_to_remove:
                if key not in self.exported_objects:
                    print('WARNING: Can not delete key "%s" from luxcore_scene' % key)
                    print("The object was probably renamed")
                    continue

                exported_thing = self.exported_objects[key]

                if exported_thing is None:
                    print('Value for key "%s" is None!' % key)
                    continue

                # exported_objects contains instances of ExportedObject and ExportedLight
                if isinstance(exported_thing, utils.ExportedObject):
                    remove_func = luxcore_scene.DeleteObject
                else:
                    remove_func = luxcore_scene.DeleteLight

                for luxcore_name in exported_thing.luxcore_names:
                    print("Deleting", luxcore_name)
                    remove_func(luxcore_name)

                del self.exported_objects[key]

            for key in self.visibility_cache.objects_to_add:
                obj = utils.obj_from_key(key, context.visible_objects)
                self._convert_object(props, obj, context.scene, context, luxcore_scene)

        if changes & Change.WORLD:
            if context.scene.world.luxcore.light == "none":
                luxcore_scene.DeleteLight(WORLD_BACKGROUND_LIGHT_NAME)
            else:
                world_props = light.convert_world(context.scene.world, context.scene)
                props.Set(world_props)

        return props
