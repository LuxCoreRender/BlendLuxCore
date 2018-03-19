from time import time
from ..bin import pyluxcore
from .. import utils
from . import (
    blender_object, caches, camera, config, duplis,
    imagepipeline, light, material, motion_blur, hair, world
)
from .light import WORLD_BACKGROUND_LIGHT_NAME


class Change:
    NONE = 0

    CONFIG = 1 << 0
    CAMERA = 1 << 1
    OBJECT = 1 << 2
    MATERIAL = 1 << 3
    VISIBILITY = 1 << 4
    WORLD = 1 << 5
    IMAGEPIPELINE = 1 << 6

    REQUIRES_SCENE_EDIT = CAMERA | OBJECT | MATERIAL | VISIBILITY | WORLD
    REQUIRES_VIEW_UPDATE = CONFIG
    REQUIRES_SESSION_PARSE = IMAGEPIPELINE

    @staticmethod
    def to_string(changes):
        s = ""
        members = [attr for attr in dir(Change) if not callable(getattr(Change, attr)) and not attr.startswith("__")]
        for changetype in members:
            if changes & getattr(Change, changetype):
                if s:
                    s += " | "
                s += changetype
        return s


class Exporter(object):
    def __init__(self):
        print("exporter init")
        self.config_cache = caches.StringCache()
        self.camera_cache = caches.CameraCache()
        self.object_cache = caches.ObjectCache()
        self.material_cache = caches.MaterialCache()
        self.visibility_cache = caches.VisibilityCache()
        self.world_cache = caches.WorldCache()
        self.imagepipeline_cache = caches.StringCache()
        # This dict contains ExportedObject and ExportedLight instances
        self.exported_objects = {}

    def create_session(self, scene, context=None, engine=None):
        # Notes:
        # In final render, context is None
        # In viewport render, engine is None (we can't show messages or check test_break() anyway)

        print("create_session")
        start = time()
        # Scene
        luxcore_scene = pyluxcore.Scene()
        scene_props = pyluxcore.Properties()

        # Camera (needs to be parsed first because it is needed for hair tesselation)
        self.camera_cache.diff(scene, context)  # Init camera cache
        luxcore_scene.Parse(self.camera_cache.props)

        # Objects and lamps
        objs = context.visible_objects if context else scene.objects
        len_objs = len(objs)

        for index, obj in enumerate(objs, start=1):
            if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT", "LAMP", "EMPTY"}:
                if engine:
                    engine.update_stats("Export", "Object: %s (%d/%d)" % (obj.name, index, len_objs))
                self._convert_object(scene_props, obj, scene, context, luxcore_scene, engine=engine)

                # Objects are the most expensive to export, so they dictate the progress
                if engine:
                    engine.update_progress(index / len_objs)
            # Regularly check if we should abort the export (important in heavy scenes)
            if engine and engine.test_break():
                return None

        # Motion blur
        if scene.camera:
            blur_settings = scene.camera.data.luxcore.motion_blur
            # Don't export camera blur in viewport
            camera_blur = blur_settings.camera_blur and not context
            enabled = blur_settings.enable and (blur_settings.object_blur or camera_blur)

            if enabled and blur_settings.shutter > 0:
                motion_blur_props, cam_moving = motion_blur.convert(context, scene, objs, self.exported_objects)

                if cam_moving:
                    # Re-export the camera with motion blur enabled
                    # (This is fast and we only have to step through the scene once in total, not twice)
                    camera_props = camera.convert(scene, context, cam_moving)
                    motion_blur_props.Set(camera_props)

                scene_props.Set(motion_blur_props)

        # World
        world_props = world.convert(scene)
        scene_props.Set(world_props)

        luxcore_scene.Parse(scene_props)

        # Regularly check if we should abort the export (important in heavy scenes)
        if engine and engine.test_break():
            return None

        # Convert config at last because all lightgroups and passes have to be already defined
        config_props = config.convert(scene, context, engine)

        if config_props is None:
            # There was a critical error in config export, we can't render
            raise Exception("Errors in config, check error log")

        # Init config cache (convert to string here because config_props gets changed below)
        self.config_cache.diff(str(config_props))

        # Imagepipeline
        imagepipeline_props = imagepipeline.convert(scene, context)
        self.imagepipeline_cache.diff(imagepipeline_props)  # Init imagepipeline cache
        # Add imagepipeline to config props
        config_props.Set(imagepipeline_props)

        # Create the renderconfig
        renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)

        # Regularly check if we should abort the export (important in heavy scenes)
        if engine and engine.test_break():
            return None

        export_time = time() - start
        print("Export took %.1fs" % export_time)

        if engine:
            if config_props.Get("renderengine.type").GetString().endswith("OCL"):
                message = "Compiling OpenCL Kernels..."
            else:
                message = "Creating RenderSession..."

            engine.update_stats("Export Finished (%.1fs)" % export_time, message)

        # Create session (in case of OpenCL engines, render kernels are compiled here)
        start = time()
        session = pyluxcore.RenderSession(renderconfig)
        elapsed_msg = "Session created in %.1fs" % (time() - start)
        print(elapsed_msg)

        return session

    def get_changes(self, scene, context=None):
        changes = Change.NONE

        if context:
            # Changes that only need to be checked in viewport render, not in final render
            config_props = config.convert(scene, context)
            if self.config_cache.diff(config_props):
                changes |= Change.CONFIG

            if self.camera_cache.diff(scene, context):
                changes |= Change.CAMERA

            if self.object_cache.diff(scene):
                changes |= Change.OBJECT

            if self.material_cache.diff():
                changes |= Change.MATERIAL

            if self.visibility_cache.diff(context):
                changes |= Change.VISIBILITY

            if self.world_cache.diff(context):
                changes |= Change.WORLD

        # Relevant during final render
        imagepipeline_props = imagepipeline.convert(scene, context)
        if self.imagepipeline_cache.diff(imagepipeline_props):
            changes |= Change.IMAGEPIPELINE

        return changes

    def update(self, context, session, changes):
        print("Update because of:", Change.to_string(changes))

        if changes & Change.CONFIG:
            # We already converted the new config settings during get_changes(), re-use them
            session = self._update_config(session, self.config_cache.props)

        if changes & Change.REQUIRES_SCENE_EDIT:
            luxcore_scene = session.GetRenderConfig().GetScene()
            session.BeginSceneEdit()

            try:
                props = self._update_scene(context, changes, luxcore_scene)
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

        if changes & Change.REQUIRES_SESSION_PARSE:
            self.update_session(changes, session)

        # We have to return and re-assign the session in the RenderEngine,
        # because it might have been replaced in _update_config()
        return session

    def update_session(self, changes, session):
        if changes & Change.IMAGEPIPELINE:
            session.Parse(self.imagepipeline_cache.props)
        # TODO: lightgroups will also be put here

    def _convert_object(self, props, obj, scene, context, luxcore_scene,
                        update_mesh=False, dupli_suffix="", engine=None):
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
                                                         update_mesh, dupli_suffix)

        # Convert particles and dupliverts/faces
        if obj.is_duplicator:
            duplis.convert(obj, scene, context, luxcore_scene, engine)

        # When moving a duplicated object, update the parent, too (concerns dupliverts/faces)
        if obj.parent and obj.parent.is_duplicator:
            self._convert_object(props, obj.parent, scene, context, luxcore_scene)

        # Convert hair
        for psys in obj.particle_systems:
            settings = psys.settings
            # render_type OBJECT and GROUP are handled by duplis.convert() above
            if settings.type == "HAIR" and settings.render_type == "PATH":
                hair.convert_hair(obj, psys, luxcore_scene, scene, context, engine)
                
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

    def _update_scene(self, context, changes, luxcore_scene):
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
                luxcore_name, mat_props = material.convert(mat, context.scene, context)
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

            world_props = world.convert(context.scene)
            props.Set(world_props)

        return props
