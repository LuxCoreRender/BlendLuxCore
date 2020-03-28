from bl_operators.presets import AddPresetBase
from bpy.types import Operator

class AddPresetLuxcore(AddPresetBase, Operator):
    '''Add an LuxCore Preset'''
    bl_idname = "render.luxcore_preset_add"
    bl_label = "Add LuxCore Preset"
    preset_menu = "LUXCORE_RENDER_PT_luxcore_presets"

    preset_defines = [
        "luxcore = bpy.context.scene.luxcore.config"
    ]

    preset_values = [
        "luxcore.preset_version",
        "luxcore.engine",
        "luxcore.sampler",
        "luxcore.path.hybridbackforward_enable",
        "luxcore.photongi.enabled",
        "luxcore.photongi.caustic_enabled",
        "luxcore.photongi.indirect_enabled",
        "luxcore.envlight_cache.enabled",
        "luxcore.dls_cache.enabled",
    ]

    preset_subdir = "BlendLuxCore"

