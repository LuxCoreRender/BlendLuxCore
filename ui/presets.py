from bl_operators.presets import AddPresetBase
from bpy.types import Operator

#class AddPresetLuxcore(AddPresetBase, Operator):
#    '''Add an LuxCore Preset'''
#    bl_idname = "render.luxcore_preset_add"
#    bl_label = "Add LuxCore Preset"
#    preset_menu = "LUXCORE_RENDER_PT_luxcore_presets"
#
#    preset_defines = [
#        "luxcore = bpy.context.scene.luxcore.config"
#    ]
#
#    preset_values = [
#        "luxcore.preset_version",
#        "luxcore.engine",
#        "luxcore.sampler",
#        "luxcore.path.hybridbackforward_enable",
#        "luxcore.photongi.enabled",
#        "luxcore.photongi.caustic_enabled",
#        "luxcore.photongi.indirect_enabled",
#        "luxcore.envlight_cache.enabled",
#        "luxcore.dls_cache.enabled"
#    ]
#
#    preset_subdir = "BlendLuxCore/Sampling"
    
class Add_Image_Pipeline_PresetLuxcore(AddPresetBase, Operator):
    '''Add an LuxCore Image Pipeline Preset'''
    bl_idname = "render.luxcore_image_pipeline_preset_add"
    bl_label = "Add LuxCore Image Pipeline Preset"
    preset_menu = "LUXCORE_RENDER_PT_luxcore_image_pipeline_presets"

    preset_defines = [
        "luxcore = bpy.context.scene.luxcore.config",
        "pipeline = bpy.pipeline = bpy.context.camera.luxcore.imagepipeline"
    ]

    preset_values = [
        "luxcore.preset_version",
        
        "pipeline.bloom.enabled",
        "pipeline.bloom.radius",
        "pipeline.bloom.weight",
        
        "pipeline.mist.enabled",
        "pipeline.mist.color",
        "pipeline.mist.amount",
        "pipeline.mist.start_distance",
        "pipeline.mist.end_distance",
        
        "pipeline.vignetting.enabled",
        "pipeline.vignetting.scale",
        
        "pipeline.coloraberration.enabled",
        "pipeline.coloraberration.amount",
        
        "pipeline.camera_response_func.enabled",
        "pipeline.camera_response_func.type",
        
        "pipeline.white_balance.enabled",
        "pipeline.white_balance.temperature"
    ]

    preset_subdir = "BlendLuxCore/ImagePipeline"

