import bpy
from time import time
from ..bin import pyluxcore
from .. import utils
from ..utils import render as utils_render
from ..utils import compatibility as utils_compatibility
from ..utils.errorlog import LuxCoreErrorLog
from . import (
    caches, camera, config,
    imagepipeline, light, material,
    motion_blur, hair, halt, world,
)
from .light import WORLD_BACKGROUND_LIGHT_NAME
from .caches.object_cache import supports_live_transform


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
    def __init__(self, stats=None):
        self.scene = None  # TODO I would like to remove this, the evaluated scene is temporary
        self.stats = stats

        self.config_cache = caches.StringCache()
        self.camera_cache = caches.CameraCache()
        # self.object_cache = caches.ObjectCache()
        self.object_cache2 = caches.ObjectCache2()
        self.material_cache = caches.MaterialCache()
        self.visibility_cache = caches.VisibilityCache()
        self.world_cache = caches.WorldCache()
        self.imagepipeline_cache = caches.StringCache()
        self.halt_cache = caches.StringCache()
        self.motion_blur_enabled = False
        
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

    def create_session(self, depsgraph, context=None, engine=None, view_layer=None):
        # Notes:
        # In final render, context is None

        print("[Exporter] Creating session")
        start = time()
        # TODO 2.8 I'm not too happy about this, we shouldn't keep any reference to temporary data, even if only for a while
        self.scene = depsgraph.scene_eval
        scene = self.scene
        stats = self.stats
        if stats:
            stats.reset()

        # We have to run the compatibility code before export because it could be that
        # the user has linked/appended assets with node trees from previous versions of
        # the addon since opening the .blend file.
        utils_compatibility.run()

        # Scene
        luxcore_scene = pyluxcore.Scene()
        scene_props = pyluxcore.Properties()

        # Camera (needs to be parsed first because it is needed for hair tesselation)
        self.camera_cache.diff(self, scene, depsgraph, context)  # Init camera cache
        luxcore_scene.Parse(self.camera_cache.props)

        if utils.is_valid_camera(scene.camera):
            blur_settings = scene.camera.data.luxcore.motion_blur
            # Don't export camera blur in viewport
            camera_blur = blur_settings.camera_blur and not context
            self.motion_blur_enabled = blur_settings.enable and (blur_settings.object_blur or camera_blur)\
                                       and (blur_settings.shutter > 0)

        # Objects and lights
        is_viewport_render = context is not None
        instances = self.object_cache2.first_run(self, depsgraph, view_layer, engine, luxcore_scene,
                                                 scene_props, is_viewport_render)
        if instances is None:
            # Export was cancelled by user
            return None

        if is_viewport_render:
            self.visibility_cache.init(depsgraph)

        # Motion blur
        # Motion blur seems not to work in viewport render, i.e. matrix_world is the same on every frame
        if not context and utils.is_valid_camera(scene.camera):
            if self.motion_blur_enabled:
                motion_blur_props, cam_moving = motion_blur.convert(context, engine, scene, depsgraph,
                                                                    self.object_cache2)

                if cam_moving:
                    # Re-export the camera with motion blur enabled
                    # (This is fast and we only have to step through the scene once in total, not twice)
                    camera_props = camera.convert(self, scene, depsgraph, context, cam_moving)
                    motion_blur_props.Set(camera_props)

                scene_props.Set(motion_blur_props)

        # World
        world_props = world.convert(self, depsgraph, scene, is_viewport_render)
        scene_props.Set(world_props)

        if scene.luxcore.debug.enabled and scene.luxcore.debug.print_properties:
            print("-" * 50)
            print("DEBUG: Scene Properties:\n")
            print("(Note: does not contain dupli props, only the props of the base object)\n")
            print(scene_props)
            print("-" * 50)
        luxcore_scene.Parse(scene_props)
        # We can only duplicate the instances *after* the scene_props were parsed so the base
        # objects are available for luxcore_scene
        self.object_cache2.duplicate_instances(instances, luxcore_scene)
        # The instances dict can be quite large, delete explicitely (TODO maybe even call gc.collect()?)
        del instances

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
            LuxCoreErrorLog.add_warning(msg)
        if stats:
            stats.light_count.value = light_count

        # Create the renderconfig
        if scene.luxcore.debug.enabled and scene.luxcore.debug.print_properties:
            print("-" * 50)
            print("DEBUG: Config Properties:\n")
            print(config_props)
            print("-" * 50)
        renderconfig = pyluxcore.RenderConfig(config_props, luxcore_scene)

        # Regularly check if we should abort the export (important in heavy scenes)
        if engine and engine.test_break():
            return None

        export_time = time() - start
        print("Export took %.1f s" % export_time)
        if stats:
            stats.export_time.value = export_time
            self._init_stats(stats, config_props, scene)

        if engine:
            message = "Creating RenderSession"
            # Inform about pre-computations that can take a long time to complete, like caches
            caches = {
                # The value in the list is used as fallback if the property is not set
                "PhotonGI": config_props.Get("path.photongi.indirect.enabled", [False]).GetBool(),
                "Caustics": config_props.Get("path.photongi.caustic.enabled", [False]).GetBool(),
                "DLSC": config_props.Get("lightstrategy.type", [""]).GetString() == "DLS_CACHE",
                "Env. Light": scene.luxcore.config.envlight_cache.enabled,
            }
            enabled_caches = [key for key, value in caches.items() if value]

            if any(enabled_caches):
                message += ", computing caches (" + ", ".join(enabled_caches) + ")"

            if config_props.Get("renderengine.type").GetString().endswith("OCL"):
                message += ", compiling OpenCL kernels"

            message += " ..."
            engine.update_stats("Export Finished (%.1f s)" % export_time, message)

        # Do not hold reference to temporary data
        self.scene = None
        return pyluxcore.RenderSession(renderconfig)

    def get_changes(self, depsgraph, context=None):
        self.scene = depsgraph.scene_eval
        scene = self.scene
        changes = Change.NONE
        final = context is None

        # Particle system counts might have changed
        supports_live_transform.cache_clear()

        if not final:
            # Changes that only need to be checked in viewport render, not in final render
            s = time()
            config_props = config.convert(self, scene, context)
            if self.config_cache.diff(config_props):
                changes |= Change.CONFIG
            print("get_changes(): checking for config changes took %.1f ms" % ((time() - s) * 1000))

            s = time()
            if self.camera_cache.diff(self, scene, depsgraph, context):
                changes |= Change.CAMERA
            print("get_changes(): checking for camera changes took %.1f ms" % ((time() - s) * 1000))

            s = time()
            if self.object_cache2.diff(depsgraph):
                changes |= Change.OBJECT
            print("get_changes(): checking for object_cache changes took %.1f ms" % ((time() - s) * 1000))

            s = time()
            if self.material_cache.diff(depsgraph):
                changes |= Change.MATERIAL
            print("get_changes(): checking for material changes took %.1f ms" % ((time() - s) * 1000))

            s = time()
            if self.visibility_cache.diff(depsgraph):
                changes |= Change.VISIBILITY
            print("get_changes(): checking for visibility changes took %.1f ms" % ((time() - s) * 1000))

            s = time()
            if self.world_cache.diff(depsgraph):
                changes |= Change.WORLD
            print("get_changes(): checking for world changes took %.1f ms" % ((time() - s) * 1000))

        # Relevant during final render
        s = time()
        imagepipeline_props = imagepipeline.convert(depsgraph.scene, context)
        if self.imagepipeline_cache.diff(imagepipeline_props):
            changes |= Change.IMAGEPIPELINE
        print("get_changes(): checking for imagepipeline changes took %.1f ms" % ((time() - s) * 1000))

        if final:
            # Halt conditions are only used during final render
            halt_props = halt.convert(depsgraph.scene)
            if self.halt_cache.diff(halt_props):
                changes |= Change.HALT

        # Do not hold reference to temporary data
        self.scene = None
        return changes

    def update(self, depsgraph, context, session, changes):
        self.scene = depsgraph.scene_eval
        print("[Exporter] Update because of:", Change.to_string(changes))
        # Invalidate node cache
        self.node_cache.clear()

        if changes & Change.CONFIG:
            # We already converted the new config settings during get_changes(), re-use them
            session = self._update_config(session, self.config_cache.props)

        if changes & Change.REQUIRES_SCENE_EDIT:
            luxcore_scene = session.GetRenderConfig().GetScene()
            session.BeginSceneEdit()

            try:
                props = self._update_scene(depsgraph, context, changes, luxcore_scene)
                luxcore_scene.Parse(props)
            except Exception as error:
                LuxCoreErrorLog.add_error(error)
                import traceback
                traceback.print_exc()

            try:
                session.EndSceneEdit()
            except RuntimeError as error:
                LuxCoreErrorLog.add_error(error)
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

        # Do not hold reference to temporary data
        self.scene = None

        # We have to return and re-assign the session in the RenderEngine,
        # because it might have been replaced in _update_config()
        return session

    def update_session(self, changes, session):
        if changes & Change.IMAGEPIPELINE:
            session.Parse(self.imagepipeline_cache.props)
        if changes & Change.HALT:
            session.Parse(self.halt_cache.props)

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

    def _update_scene(self, depsgraph, context, changes, luxcore_scene):
        props = pyluxcore.Properties()

        if changes & Change.CAMERA:
            # We already converted the new camera settings during get_changes(), re-use them
            props.Set(self.camera_cache.props)

        if changes & Change.OBJECT:
            self.object_cache2.update(self, depsgraph, luxcore_scene, props)

        if changes & Change.MATERIAL:
            # for mat in self.material_cache.changed_materials:
            #     luxcore_name, mat_props = material.convert(self, mat, context.scene, context)
            #     props.Set(mat_props)
            self.material_cache.update(self, depsgraph, context, props)

        if changes & Change.VISIBILITY:
            for key in self.visibility_cache.objects_to_remove:
                print("Removing object with key", key)

                try:
                    exported_obj = self.object_cache2.exported_objects.pop(key)
                    exported_obj.delete(luxcore_scene)
                except KeyError:
                    # This is ok, not every exportable object is added to exported_objects
                    pass

            if self.visibility_cache.objects_to_remove:
                # luxcore_scene.RemoveUnusedMeshes()  # TODO for some reason this deletes even some meshes that are still in use
                luxcore_scene.RemoveUnusedMaterials()
                luxcore_scene.RemoveUnusedTextures()
                luxcore_scene.RemoveUnusedImageMaps()

        if changes & Change.WORLD:
            if not context.scene.world or context.scene.world.luxcore.light == "none":
                luxcore_scene.DeleteLight(WORLD_BACKGROUND_LIGHT_NAME)

            world_props = world.convert(self, depsgraph, context.scene, is_viewport_render=True)
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
