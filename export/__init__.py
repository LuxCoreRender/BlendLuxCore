import bpy
from ..bin import pyluxcore


class CacheEntry(object):
    def __init__(self, luxcore_names, props):
        self.luxcore_names = luxcore_names
        self.props = props
        self.is_updated = True  # new entries are flagged as updated


def make_key(datablock):
    key = datablock.name
    if datablock.library:
        key += datablock.library.name
    return key


class Exporter(object):
    def __init__(self):
        print("exporter init")
        self.settings = SettingsCache()

    def __del__(self):
        print("exporter del")

    def create_session(self, scene, context=None):
        print("create_session")
        # Scene
        luxcore_scene = pyluxcore.Scene()
        scene_props = pyluxcore.Properties()

        # Camera (needs to be parsed first because it is needed for hair tesselation)
        camera_props = camera.convert(scene, context)
        luxcore_scene.Parse(camera_props)

        # for obj in context.scene.objects:
        #     entry = Cache.get_entry(obj)
        #     if entry:
        #         scene_props.Set(entry.props)

        # Testlight
        # scene_props.Set(pyluxcore.Property("scene.lights.test.type", "sky"))
        # scene_props.Set(pyluxcore.Property("scene.lights.test.dir", [-0.5, -0.5, 0.5]))
        # scene_props.Set(pyluxcore.Property("scene.lights.test.turbidity", [2.2]))
        # scene_props.Set(pyluxcore.Property("scene.lights.test.gain", [1.0, 1.0, 1.0]))

        scene_props.Set(pyluxcore.Property('scene.lights.' + 'test' + '.type', 'infinite'))
        scene_props.Set(pyluxcore.Property('scene.lights.' + 'test' + '.file', "F:\\Users\\Simon_2\\Projekte\\Blender\\00_Resources\HDRIs\\03-Ueno-Shrine_3k.hdr"))

        luxcore_scene.Parse(scene_props)

        # Config
        config_props = config.convert(context.scene, context)
        luxcore_config = pyluxcore.RenderConfig(config_props, luxcore_scene)

        # Session
        return pyluxcore.RenderSession(luxcore_config)

    def needs_draw_update(self, context):
        """Special method for view_draw() call, only checks camera and config updates"""
        self.settings.check_camera_update(camera.convert(context.scene, context))

    def needs_update(self, context):
        print("needs_update")

        # Check which scene elements need an update
        self.settings.check_camera_update(camera.convert(context.scene, context))

    def execute_update(self, context, session):
        print("execute_update")

        if self.settings.needs_config_update():
            pass
            # TODO

        if self.settings.needs_scene_update():
            luxcore_scene = session.GetRenderConfig().GetScene()
            session.BeginSceneEdit()
            props = pyluxcore.Properties()

            if self.settings.update_camera:
                props.Set(camera.convert(context.scene, context))

            print("new props:")
            print(props)

            luxcore_scene.Parse(props)
            session.EndSceneEdit()

        if self.settings.needs_session_update():
            pass
            # TODO

        self.settings.clear_update_flags()

    # TODO: method for updates during final render (session.Parse()) - if possible shared with viewport render



class SettingsCache(object):
    def __init__(self):
        self.config = ""
        self.update_config = False

        self.camera = ""
        self.update_camera = False

    def needs_config_update(self):
        return self.update_config

    def needs_scene_update(self):
        return self.update_camera # TODO or update_object or ...

    def needs_session_update(self):
        return False # TODO

    def clear_update_flags(self):
        # TODO: improve this
        self.update_camera = False

    def check_camera_update(self, props):
        str_props = str(props)
        self.update_camera = self.camera != str_props
        if self.update_camera:
            self.camera = str_props
