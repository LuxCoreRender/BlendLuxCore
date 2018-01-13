from time import time
from array import array
import bpy
from ..bin import pyluxcore
from .. import utils
from mathutils import Matrix
from ..utils import node as utils_node
from . import blender_object, camera, config, light, material, motion_blur
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


class Exporter(object):
    def __init__(self):
        print("exporter init")
        self.config_cache = caches.StringCache()
        self.camera_cache = caches.StringCache()
        self.object_cache = caches.ObjectCache()
        self.material_cache = caches.MaterialCache()
        self.visibility_cache = caches.VisibilityCache()
        self.world_cache = caches.WorldCache()
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
                self._convert_object(scene_props, obj, scene, context, luxcore_scene, engine)


                if obj.is_duplicator:
                    print("Duplicator")
                    start = time()

                    mode = 'VIEWPORT' if context else 'RENDER'
                    obj.dupli_list_create(scene, settings=mode)

                    name_prefix = utils.get_unique_luxcore_name(obj)
                    exported = {}

                    class Duplis:
                        def __init__(self, exported_obj, matrix):
                            self.exported_obj = exported_obj
                            self.matrices = matrix
                            self.count = 1

                        def add(self, matrix):
                            self.matrices.extend(matrix)
                            self.count += 1

                    for dupli in obj.dupli_list:
                        # Use the utils functions to build names so linked objects work (libraries)
                        name = name_prefix + utils.get_unique_luxcore_name(dupli.object)
                        matrix_list = utils.matrix_to_list(dupli.matrix, scene, apply_worldscale=True)

                        try:
                            # Already exported, just update the Duplis info
                            exported[name].add(matrix_list)
                        except KeyError:
                            # Not yet exported
                            name_suffix = name_prefix + str(dupli.index)
                            if dupli.particle_system:
                                name_suffix += utils.to_luxcore_name(dupli.particle_system.name)

                            exported_obj = self._convert_object(scene_props, dupli.object, scene, context,
                                                                luxcore_scene, update_mesh=True,
                                                                dupli_suffix=name_suffix)
                            print("exported:", name)
                            exported[name] = Duplis(exported_obj, matrix_list)
                            print("exported_obj:", exported_obj.luxcore_names)

                    obj.dupli_list_clear()
                    # Need to parse so we have the dupli objects available for DuplicateObject
                    luxcore_scene.Parse(scene_props)

                    for duplis in exported.values():
                        # Objects might be split if they have multiple materials
                        for src_name in duplis.exported_obj.luxcore_names:
                            dst_name = src_name + "dupli"
                            count = duplis.count
                            transformations = array("f", duplis.matrices)
                            luxcore_scene.DuplicateObject(src_name, dst_name, count, transformations)

                            # TODO: support steps and times (motion blur)
                            # steps = 0 # TODO
                            # times = array("f", [])
                            # luxcore_scene.DuplicateObject(src_name, dst_name, count, steps, times, transformations)

                    print("Dupli export took %.3fs" % (time() - start))
                    

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
                    # We have to set the camera props again because otherwise
                    # they get deleted because we set the camera motion props
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

    def _convert_object(self, props, obj, scene, context, luxcore_scene,
                        update_mesh=False, dupli_suffix="", matrix=None, engine=None):
        key = utils.make_key(obj)
        old_exported_obj = None

        if key not in self.exported_objects:
            # We have to update the mesh because the object was not yet exported
            update_mesh = True
        
        if not update_mesh:
            # We need the previously exported mesh defintions
            old_exported_obj = self.exported_objects[key]

        # Note: exported_obj can also be an instance of ExportedLight, but they behave the same
        obj_props, exported_obj = blender_object.convert(obj, scene, context, luxcore_scene, old_exported_obj,
                                                         update_mesh, dupli_suffix, matrix)

        if obj.is_duplicator:
            duplis.convert(obj, scene, context, luxcore_scene, engine)

        if obj.parent and obj.parent.is_duplicator:
            self._convert_object(props, obj.parent, scene, context, luxcore_scene)

        if exported_obj is None:
            # Object is not visible or an error happened.
            # In case of an error, it was already reported by blender_object.convert()
            return

        props.Set(obj_props)
        self.exported_objects[key] = exported_obj
        return exported_obj

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
