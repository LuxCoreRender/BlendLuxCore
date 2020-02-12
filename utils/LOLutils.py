import bpy
import os

LUXCOREASSETS_LOCAL = "http://localhost:8001"
LUXCOREASSETS_MAIN = "https://draviastudio.com/"

def get_search_props():
    scene = bpy.context.scene
    if scene is None:
        return;
    uiprops = scene.blenderkitUI
    props = None
    if uiprops.asset_type == 'MODEL':
        if not hasattr(scene, 'LuxCoreAssets_models'):
            return;
        props = scene.blenderkit_models
    if uiprops.asset_type == 'SCENE':
        if not hasattr(scene, 'LuxCoreAssets_scene'):
            return;
        props = scene.blenderkit_scene
    if uiprops.asset_type == 'MATERIAL':
        if not hasattr(scene, 'LuxCoreAssets_mat'):
            return;
        props = scene.blenderkit_mat

    if uiprops.asset_type == 'TEXTURE':
        if not hasattr(scene, 'LuxCoreAssets_tex'):
            return;
        # props = scene.blenderkit_tex

    if uiprops.asset_type == 'BRUSH':
        if not hasattr(scene, 'LuxCoreAssets_brush'):
            return;
        props = scene.blenderkit_brush
    return props

def save_prefs(self, context):
    # first check context, so we don't do this on registration or blender startup
    if not bpy.app.background: #(hasattr kills blender)
        # TODO:
        #user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
        test = 1
        #prefs = {
        #    'global_dir': user_preferences.global_dir,
        #}
        #try:
        #    fpath = paths.BLENDERKIT_SETTINGS_FILENAME
        #    if not os.path.exists(paths._presets):
        #        os.makedirs(paths._presets)
        #    f = open(fpath, 'w')
        #    with open(fpath, 'w') as s:
        #        json.dump(prefs, s)
        #except Exception as e:
        #    print(e)

def default_global_dict():
    from os.path import expanduser
    home = expanduser("~")
    return home + os.sep + 'LuxCoreAssets_data'