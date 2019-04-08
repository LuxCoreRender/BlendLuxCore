import bpy
from time import time
from ..bin import pyluxcore
from .. import utils
from ..utils import render as utils_render
from ..utils import compatibility as utils_compatibility
from . import (
    blender_object, caches, camera, config, duplis,
    group_instance, imagepipeline, light, material,
    motion_blur, hair, halt, world,
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
    HALT = 1 << 7

    REQUIRES_SCENE_EDIT = CAMERA | OBJECT | MATERIAL | VISIBILITY | WORLD
    REQUIRES_VIEW_UPDATE = CONFIG
    REQUIRES_SESSION_PARSE = IMAGEPIPELINE | HALT

    @staticmethod
    def to_string(changes):
        s = ""
        members = [attr for attr in dir(Change) if not callable(getattr(Change, attr)) and not attr.startswith("__")]
        for changetype in members:
            if changes & getattr(Change, changetype):
                if s:
                    s += " | "
                s += changetype

        return s if changes else "NONE"


class Exporter(object):
    def __init__(self, blender_scene, stats=None):
        self.scene = blender_scene
        self.stats = stats

        self.config_cache = caches.StringCache()
        self.camera_cache = caches.CameraCache()
        self.object_cache = caches.ObjectCache()
        self.material_cache = caches.MaterialCache()
        self.visibility_cache = caches.VisibilityCache()
        self.world_cache = caches.WorldCache()
        self.imagepipeline_cache = caches.StringCache()
        self.halt_cache = caches.StringCache()
        # This dict contains ExportedObject and ExportedLight instances
        self.exported_objects = {}
        # Contains mesh_definitions for multi-user meshes.
        # Keys are made with utils.make_key(blender_obj.data)
        self.shared_meshes = {}

        self.dupli_groups = {}

        # A dictionary with the following mapping:
        # {node_key: luxcore_name}
        # Most of the time node_key == luxcore_name, but some nodes have to insert
        # implicit textures n front of themselves which changes their luxcore_name.
        # Avoids re-exporting the same node multiple times.
        # TODO: currently the node cache has to be cleared when an output node starts
        # to export, because we don't have one global properties object.
        self.node_cache = {}

        # If a light/material uses a lightgroup, the id is stored here during export
        self.lightgroup_cache = set()

        self.objs_updated_by_export = set()
        self.mats_updated_by_export = set()

    def create_session(self, context=None, engine=None):
        # Notes:
        # In final render, context is None
        # In viewport render, engine is None (we can't show messages or check test_break() anyway)

        print("[Exporter] Creating session")
        start = time()
        scene = self.scene
        stats = self.stats
        if stats:
            stats.reset()
        updated_objs_pre = self.object_cache.diff(scene)
        updated_mats_pre = self.material_cache.diff()

        # We have to run the compatibility code before export because it could be that
        # the user has linked/appended assets with node trees from previous versions of
        # the addon since opening the .blend file.
        utils_compatibility.run()

        # Scene
        luxcore_scene = pyluxcore.Scene()
        scene_props = pyluxcore.Properties()

        # Camera (needs to be parsed first because it is needed for hair tesselation)
        self.camera_cache.diff(self, scene, context)  # Init camera cache
        luxcore_scene.Parse(self.camera_cache.props)

        # Objects and lamps
        objs = context.visible_objects if context else scene.objects
        len_objs = len(objs)

        for index, obj in enumerate(objs, start=1):
            if obj.type in blender_object.EXPORTABLE_OBJECTS:
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
        if utils.is_valid_camera(scene.camera):
            blur_settings = scene.camera.data.luxcore.motion_blur
            # Don't export camera blur in viewport
            camera_blur = blur_settings.camera_blur and not context
            enabled = blur_settings.enable and (blur_settings.object_blur or camera_blur)

            if enabled and blur_settings.shutter > 0:
                motion_blur_props, cam_moving = motion_blur.convert(context, scene, objs, self.exported_objects)

                if cam_moving:
                    # Re-export the camera with motion blur enabled
                    # (This is fast and we only have to step through the scene once in total, not twice)
                    camera_props = camera.convert(self, scene, context, cam_moving)
                    motion_blur_props.Set(camera_props)

                scene_props.Set(motion_blur_props)

        # World
        world_props = world.convert(self, scene)
        scene_props.Set(world_props)

        luxcore_scene.Parse(scene_props)

        # Regularly check if we should abort the export (important in heavy scenes)
        if engine and engine.test_break():
            return None

        # Convert config at last because all lightgroups and passes have to be already defined
        config_props = config.convert(self, scene, context, engine)
        if str(config_props) == "":
            # Config props are empty: there was a critical error in config export, we can't render
            raise Exception("Errors in config, check error log")

        # Init config cache (convert to string here because config_props gets changed below)
        self.config_cache.diff(str(config_props))

        # Imagepipeline
        imagepipeline_props = imagepipeline.convert(scene, context)
        self.imagepipeline_cache.diff(imagepipeline_props)  # Init imagepipeline cache
        # Add imagepipeline to config props
        config_props.Set(imagepipeline_props)

        # Halt conditions
        halt_props = halt.convert(scene)
        self.halt_cache.diff(halt_props)
        config_props.Set(halt_props)

        light_count = luxcore_scene.GetLightCount()
        if light_count > 1000:
            msg = "The scene contains a lot of light sources (%d), performance might suffer" % light_count
            scene.luxcore.errorlog.add_warning(msg)
        if stats:
            stats.light_count.value = light_count

        # Create the renderconfig
        self._print_debug_info(scene, config_props, luxcore_scene)
        renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)

        # Check which objects were flagged for update by our own export,
        # these should not be considered for the next viewport update.
        self.objs_updated_by_export = self.object_cache.diff(scene) - updated_objs_pre
        self.mats_updated_by_export = self.material_cache.diff() - updated_mats_pre

        # Regularly check if we should abort the export (important in heavy scenes)
        if engine and engine.test_break():
            return None

        export_time = time() - start
        print("Export took %.1f s" % export_time)
        if stats:
            stats.export_time.value = export_time
            self._init_stats(stats, config_props, scene)

        if engine:
            if config_props.Get("renderengine.type").GetString().endswith("OCL"):
                message = "Creating RenderSession and compiling OpenCL kernels..."
            else:
                message = "Creating RenderSession..."

            engine.update_stats("Export Finished (%.1f s)" % export_time, message)

        session = pyluxcore.RenderSession(renderconfig)
        return session

    def get_changes(self, context=None):
        scene = self.scene
        changes = Change.NONE
        final = context is None

        if not final:
            # Changes that only need to be checked in viewport render, not in final render
            config_props = config.convert(self, scene, context)
            if self.config_cache.diff(config_props):
                changes |= Change.CONFIG

            if self.camera_cache.diff(self, scene, context):
                changes |= Change.CAMERA

            if self.object_cache.diff(scene, self.objs_updated_by_export):
                changes |= Change.OBJECT

            if self.material_cache.diff(self.mats_updated_by_export):
                changes |= Change.MATERIAL

            if self.visibility_cache.diff(context):
                changes |= Change.VISIBILITY

            if self.world_cache.diff(context):
                changes |= Change.WORLD

        # Relevant during final render
        imagepipeline_props = imagepipeline.convert(scene, context)
        if self.imagepipeline_cache.diff(imagepipeline_props):
            changes |= Change.IMAGEPIPELINE

        if final:
            # Halt conditions are only used during final render
            halt_props = halt.convert(scene)
            if self.halt_cache.diff(halt_props):
                changes |= Change.HALT

        return changes

    def update(self, context, session, changes):
        print("[Exporter] Update because of:", Change.to_string(changes))
        # Invalidate node cache
        self.node_cache.clear()
        self.shared_meshes.clear()
        self.dupli_groups.clear()

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

        self.objs_updated_by_export.clear()
        self.mats_updated_by_export.clear()

        # We have to return and re-assign the session in the RenderEngine,
        # because it might have been replaced in _update_config()
        return session

    def update_session(self, changes, session):
        if changes & Change.IMAGEPIPELINE:
            session.Parse(self.imagepipeline_cache.props)
        if changes & Change.HALT:
            session.Parse(self.halt_cache.props)

    def _convert_object(self, props, obj, scene, context, luxcore_scene,
                        update_mesh=False, dupli_suffix="", engine=None,
                        check_dupli_parent=False):
        key = utils.make_key(obj)
        old_exported_obj = None

        if key not in self.exported_objects:
            # We have to update the mesh because the object was not yet exported
            update_mesh = True
        
        if not update_mesh:
            # We need the previously exported mesh defintions
            old_exported_obj = self.exported_objects[key]

        # Note: exported_obj can also be an instance of ExportedLight, but they behave the same
        obj_props, exported_obj = blender_object.convert(self, obj, scene, context, luxcore_scene, old_exported_obj,
                                                         update_mesh, dupli_suffix)

        # Convert particles and dupliverts/faces
        if obj.is_duplicator:
            if obj.dupli_type == "GROUP":
                group_instance.convert(self, obj, scene, context, luxcore_scene, props)
            else:
                duplis.convert(self, obj, scene, context, luxcore_scene, engine)

        # When moving a duplicated object, update the parent, too (concerns dupliverts/faces)
        if check_dupli_parent and obj.parent and obj.parent.is_duplicator:
            self._convert_object(props, obj.parent, scene, context, luxcore_scene,
                                 update_mesh, dupli_suffix, engine, check_dupli_parent)

        # Convert hair
        for psys in obj.particle_systems:
            settings = psys.settings
            # render_type OBJECT and GROUP are handled by duplis.convert() above
            if settings.type == "HAIR" and settings.render_type == "PATH":
                hair.convert_hair(self, obj, psys, luxcore_scene, scene, context, engine)
                
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
            print("[Exporter] ERROR: not a valid luxcore config")
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
                self._convert_object(props, obj, context.scene, context, luxcore_scene, update_mesh=False,
                                     check_dupli_parent=True)

            for obj in self.object_cache.changed_mesh:
                print("mesh changed:", obj.name)
                self._convert_object(props, obj, context.scene, context, luxcore_scene, update_mesh=True,
                                     check_dupli_parent=True)

            for obj in self.object_cache.changed_lights:
                print("light changed:", obj.name)
                self._convert_object(props, obj, context.scene, context, luxcore_scene,
                                     check_dupli_parent=True)

        if changes & Change.MATERIAL:
            for mat in self.material_cache.changed_materials:
                luxcore_name, mat_props = material.convert(self, mat, context.scene, context)
                props.Set(mat_props)

        if changes & Change.VISIBILITY:
            for key in self.visibility_cache.objects_to_remove:
                if key not in self.exported_objects:
                    print('[Exporter] WARNING: Can not delete key "%s" from luxcore_scene' % key)
                    print("The object was probably renamed")
                    continue

                exported_thing = self.exported_objects[key]

                if exported_thing is None:
                    print('[Exporter] Value for key "%s" is None!' % key)
                    continue

                # exported_objects contains instances of ExportedObject and ExportedLight
                if isinstance(exported_thing, utils.ExportedObject):
                    remove_func = luxcore_scene.DeleteObject
                else:
                    remove_func = luxcore_scene.DeleteLight

                for luxcore_name in exported_thing.luxcore_names:
                    print("[Exporter] Deleting", luxcore_name)
                    remove_func(luxcore_name)

                del self.exported_objects[key]

            for key in self.visibility_cache.objects_to_add:
                obj = utils.obj_from_key(key, context.visible_objects)
                self._convert_object(props, obj, context.scene, context, luxcore_scene)

        if changes & Change.WORLD:
            if not context.scene.world or context.scene.world.luxcore.light == "none":
                luxcore_scene.DeleteLight(WORLD_BACKGROUND_LIGHT_NAME)

            world_props = world.convert(self, context.scene)
            props.Set(world_props)

        return props

    def _init_stats(self, stats, config_props, scene):
        render_engine = config_props.Get("renderengine.type").GetString()
        stats.render_engine.value = utils_render.engine_to_str(render_engine)
        sampler = config_props.Get("sampler.type").GetString()
        stats.sampler.value = utils_render.sampler_to_str(sampler)

        config_settings = scene.luxcore.config
        path_settings = config_settings.path

        stats.light_strategy.value = utils_render.light_strategy_to_str(config_settings.light_strategy)

        if render_engine == "BIDIRCPU":
            path_depths = (
                config_settings.bidir_path_maxdepth,
                config_settings.bidir_light_maxdepth,
            )
        else:
            path_depths = (
                path_settings.depth_total,
                path_settings.depth_diffuse,
                path_settings.depth_glossy,
                path_settings.depth_specular,
            )
        stats.path_depths.value = path_depths

        if path_settings.use_clamping:
            stats.clamping.value = path_settings.clamping
        else:
            stats.clamping.value = 0

    def _print_debug_info(self, scene, config_props, luxcore_scene):
        if scene.luxcore.debug.enabled and scene.luxcore.debug.print_properties:
            print("-" * 50)
            print("DEBUG: Config Properties:\n")
            print(config_props)
            print("DEBUG: Scene Properties:\n")
            print(luxcore_scene.ToProperties())
            print("-" * 50)
