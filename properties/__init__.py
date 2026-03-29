_needs_reload = "bpy" in locals()

import bpy
from .. import utils
from . import (
    aovs,
    image_user,
    hair,
    blender_object,
    imagepipeline,
    camera,
    config,
    debug,
    denoiser,
    devices,
    display,
    halt,
    ies,
    light,
    lightgroups,
    material,
    viewport,
    statistics,
    scene,
    view_layer,
    world,
    lol,
)

# TODO
from .ies import LuxCoreIESProps

if _needs_reload:
    import importlib

    # Caveat: module order matters (due to PointerProperty and PropertyGroup)
    modules = (
        aovs,
        image_user,
        hair,
        blender_object,
        imagepipeline,
        camera,
        config,
        debug,
        denoiser,
        devices,
        display,
        halt,
        ies,
        light,
        lightgroups,
        material,
        viewport,
        statistics,
        scene,
        view_layer,
        world,
        lol,
    )
    for module in modules:
        importlib.reload(module)


# Warning: order matters, for correct loading and reloading
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
    world.LuxCoreWorldProps,
)

submodules = (lol,)


def register():
    utils.register_module("Properties", classes, submodules)


def unregister():
    utils.unregister_module("Properties", classes, submodules)
