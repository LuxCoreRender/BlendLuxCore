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
        "luxcore.path.depth_total",
        "luxcore.path.depth_diffuse",
        "luxcore.path.depth_glossy",
        "luxcore.path.depth_specular",
        "luxcore.path.use_clamping",
        "luxcore.path.clamping",
        "luxcore.light_strategy",
        "luxcore.seed",
        "luxcore.sampler",
        "luxcore.sobol_adaptive_strength",
        "luxcore.noise_estimation.warmup",
        "luxcore.noise_estimation.step",
        "luxcore.filter",
        "luxcore.filter_width"
    ]

    preset_subdir = "BlendLuxCore"

