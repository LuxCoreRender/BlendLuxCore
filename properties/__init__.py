_needs_reload = "bpy" in locals()

import bpy
from bpy.utils import register_class, unregister_class
from . import (
    aovs, blender_object, image_user, imagepipeline, camera,
    config, debug, denoiser, devices, display, hair, halt,
    ies, light, lightgroups, material, scene, statistics,
    view_layer, viewport, world, lol,
)

if _needs_reload:
    import importlib
    modules = (
        aovs, blender_object, image_user, imagepipeline, camera,
        config, debug, denoiser, devices, display, hair, halt,
        ies, light, lightgroups, material, scene, statistics,
        view_layer, viewport, world, lol,
    )
    for module in modules:
        importlib.reload(module)


classes = (
    aovs.LuxCoreAOVSettings,
    image_user.LuxCoreImageUser,
    hair.LuxCoreHair,
    blender_object.LuxCoreObjectProps,
    imagepipeline.LuxCoreImagepipelineTonemapper,
    imagepipeline.LuxCoreImagepipelineBloom,
    imagepipeline.LuxCoreImagepipelineMist,
    imagepipeline.LuxCoreImagepipelineVignetting,
    imagepipeline.LuxCoreImagepipelineColorAberration,
    imagepipeline.LuxCoreImagepipelineBackgroundImage,
    imagepipeline.LuxCoreImagepipelineWhiteBalance,
    imagepipeline.LuxCoreImagepipelineCameraResponseFunc,
    imagepipeline.LuxCoreImagepipelineColorLUT,
    imagepipeline.LuxCoreImagepipelineContourLines,
    imagepipeline.LuxCoreImagepipeline,
    camera.LuxCoreMotionBlur,
    camera.LuxCoreBokeh,
    camera.LuxCoreCameraProps,
    config.LuxCoreConfigPath,
    config.LuxCoreConfigTile,
    config.LuxCoreConfigDLSCache,
    config.LuxCoreConfigPhotonGI,
    config.LuxCoreConfigEnvLightCache,
    config.LuxCoreConfigNoiseEstimation,
    config.LuxCoreConfigImageResizePolicy,
    config.LuxCoreConfig,
    debug.LuxCoreDebugSettings,
    denoiser.LuxCoreDenoiser,
    devices.LuxCoreOpenCLDevice,
    devices.LuxCoreDeviceSettings,
    display.LuxCoreDisplaySettings,
    hair.LuxCoreParticlesProps,
    halt.LuxCoreHaltConditions,
    ies.LuxCoreIESProps,
    light.LuxCoreLightProps,
    lightgroups.LuxCoreLightGroup,
    lightgroups.LuxCoreLightGroupSettings,
    material.LuxCoreMaterialPreviewProps,
    material.LuxCoreMaterialProps,
    viewport.LuxCoreViewportSettings,
    statistics.LuxCoreRenderStatsCollection,
    scene.LuxCoreScene,
    view_layer.LuxCoreViewLayer,
    world.LuxCoreWorldProps
)

def register():
    lol.register()

    for cls in classes:
        register_class(cls)

def unregister():
    lol.unregister()

    for cls in classes:
        unregister_class(cls)
