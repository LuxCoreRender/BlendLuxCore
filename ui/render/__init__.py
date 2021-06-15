from bpy.utils import register_class, unregister_class
from . import caches, config, debug, denoiser, devices, errorlog, halt, image_resize_policy, sampling, tools, viewport

classes = (
    caches.LUXCORE_RENDER_PT_caches,
    caches.LUXCORE_RENDER_PT_caches_photongi,
    caches.LUXCORE_RENDER_PT_caches_photongi_indirect,
    caches.LUXCORE_RENDER_PT_caches_photongi_caustic,
    caches.LUXCORE_RENDER_PT_caches_photongi_persistence,
    caches.LUXCORE_RENDER_PT_caches_envlight,
    caches.LUXCORE_RENDER_PT_caches_envlight_persistence,
    caches.LUXCORE_RENDER_PT_caches_DLSC,
    caches.LUXCORE_RENDER_PT_caches_DLSC_advanced,
    caches.LUXCORE_RENDER_PT_caches_DLSC_persistence,
    config.LUXCORE_RENDER_PT_lightpaths,
    config.LUXCORE_RENDER_PT_lightpaths_bounces,
    config.LUXCORE_RENDER_PT_add_light_tracing,
    config.LUXCORE_RENDER_PT_lightpaths_clamping,
    debug.LUXCORE_RENDER_PT_debug_settings,
    denoiser.LUXCORE_RENDER_PT_denoiser,
    denoiser.LUXCORE_RENDER_PT_denoiser_bcd_advanced,
    devices.LUXCORE_RENDER_PT_devices,
    devices.LUXCORE_RENDER_PT_gpu_devices,
    devices.LUXCORE_RENDER_PT_cpu_devices,
    errorlog.LUXCORE_RENDER_PT_error_log,
    halt.LUXCORE_RENDER_PT_halt_conditions,
    halt.LUXCORE_RENDERLAYER_PT_halt_conditions,
    sampling.LUXCORE_RENDER_PT_sampling,
    sampling.LUXCORE_RENDER_PT_sampling_tiled_multipass,
    sampling.LUXCORE_RENDER_PT_sampling_adaptivity,
    sampling.LUXCORE_RENDER_PT_sampling_pixel_filtering,
    sampling.LUXCORE_RENDER_PT_sampling_advanced,
    image_resize_policy.LUXCORE_RENDER_PT_image_resize_policy,
    tools.LUXCORE_RENDER_PT_tools,
    tools.LUXCORE_RENDER_PT_filesaver,
    viewport.LUXCORE_RENDER_PT_viewport_settings,
    viewport.LUXCORE_RENDER_PT_viewport_settings_denoiser,
    viewport.LUXCORE_RENDER_PT_viewport_settings_advanced,
)

def register():
    config.register()

    for cls in classes:
        register_class(cls)

def unregister():
    config.unregister()

    for cls in classes:
        unregister_class(cls)
