import bpy
from ..bin import pyluxcore
from . import camera, config, blender_object

# TODO do I need this?
class CacheEntry(object):
    def __init__(self, luxcore_names, props):
        self.luxcore_names = luxcore_names
        self.props = props
        self.is_updated = True  # new entries are flagged as updated


# TODO maybe move to utils?
def make_key(datablock):
    key = datablock.name
    if hasattr(datablock, "type"):
        key += datablock.type
    if datablock.library:
        key += datablock.library.name
    return key


class Change:
    NONE = 0

    CONFIG = 1 << 0
    CAMERA = 1 << 1
    OBJECT = 1 << 2

    REQUIRES_SCENE_EDIT = CAMERA | OBJECT
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
                        if obj.data is not None and obj.data.is_updated:
                            self.changed_mesh.append(obj)
                        else:
                            self.changed_transform.append(obj)
                    elif obj.type == "LAMP":
                        self.lamps.append(obj)

        return self.changed_transform or self.changed_mesh or self.lamps


class Exporter(object):
    def __init__(self):
        print("exporter init")
        self.config_cache = StringCache()
        self.camera_cache = StringCache()
        self.object_cache = ObjectCache()

    def create_session(self, scene, context=None):
        print("create_session")
        # Scene
        luxcore_scene = pyluxcore.Scene()
        scene_props = pyluxcore.Properties()

        # Camera (needs to be parsed first because it is needed for hair tesselation)
        camera_props = camera.convert(scene, context)
        self.camera_cache.diff(camera_props)  # Init camera cache
        luxcore_scene.Parse(camera_props)

        objs = context.visible_objects if context else bpy.data.objects

        for obj in objs:
            if obj.type in ("MESH", "CURVE", "SURFACE", "META", "FONT"):
                scene_props.Set(blender_object.convert(obj, scene, context, luxcore_scene))

        # Testlight
        scene_props.Set(pyluxcore.Property("scene.lights.test.type", "sky"))
        scene_props.Set(pyluxcore.Property("scene.lights.test.dir", [-0.5, -0.5, 0.5]))
        scene_props.Set(pyluxcore.Property("scene.lights.test.turbidity", [2.2]))
        scene_props.Set(pyluxcore.Property("scene.lights.test.gain", [1.0, 1.0, 1.0]))
        # Another testlight
        # scene_props.Set(pyluxcore.Property("scene.lights." + "test" + ".type", "infinite"))
        # scene_props.Set(pyluxcore.Property("scene.lights." + "test" + ".file", "F:\\Users\\Simon_2\\Projekte\\Blender\\00_Resources\HDRIs\\03-Ueno-Shrine_3k.hdr"))

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

        return changes

    def _update_config(self, session, config_props):
        print("NOT UPDATING CONFIG")
        # TODO: hangs/crashes blender...
        # renderconfig = session.GetRenderConfig()
        # session.Stop()
        # renderconfig.Parse(config_props)
        # if renderconfig is None:
        #     print("ERROR: not a valid luxcore config")
        #     return
        # session = pyluxcore.RenderSession(renderconfig)
        # session.Start()

    def update(self, context, session, changes):
        if changes & Change.CONFIG:
            # We already converted the new config settings during get_changes(), re-use them
            self._update_config(session, self.config_cache.props)

        if changes & Change.REQUIRES_SCENE_EDIT:
            luxcore_scene = session.GetRenderConfig().GetScene()
            session.BeginSceneEdit()
            props = pyluxcore.Properties()

            if changes & Change.CAMERA:
                # We already converted the new camera settings during get_changes(), re-use them
                props.Set(self.camera_cache.props)

            if changes & Change.OBJECT:
                for obj in self.object_cache.changed_transform:
                    # TODO only update transform
                    print("transformed:", obj.name)
                    props.Set(blender_object.convert(obj, context.scene, context, luxcore_scene))

                for obj in self.object_cache.changed_mesh:
                    print("mesh changed:", obj.name)
                    props.Set(blender_object.convert(obj, context.scene, context, luxcore_scene))

                for obj in self.object_cache.lamps:
                    print("lamp changed:", obj.name)
                    # TODO update lamps
                    props.Set(blender_object.convert(obj, context.scene, context, luxcore_scene))

            luxcore_scene.Parse(props)
            session.EndSceneEdit()
