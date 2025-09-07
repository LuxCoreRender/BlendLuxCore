_needs_reload = "bpy" in locals()

import bpy

from bpy.utils import register_class, unregister_class


from . import (
    addon_preferences,
    blender_hair_curves,
    blender_object,
    camera,
    image_tools,
    light,
    material,
    node_editor,
    output,
    particle,
    physics,
    scene_lightgroups,
    scene_units,
    texture,
    view_layer,
    view_layer_aovs,
    volume,
    world,
    lol,
    render,
)


if _needs_reload:
    import importlib

    addon_preferences = importlib.reload(addon_preferences)
    blender_hair_curves = importlib.reload(blender_hair_curves)
    blender_object = importlib.reload(blender_object)
    camera = importlib.reload(camera)
    image_tools = importlib.reload(image_tools)
    light = importlib.reload(light)
    material = importlib.reload(material)
    node_editor = importlib.reload(node_editor)
    output = importlib.reload(output)
    particle = importlib.reload(particle)
    physics = importlib.reload(physics)
    scene_lightgroups = importlib.reload(scene_lightgroups)
    scene_units = importlib.reload(scene_units)
    texture = importlib.reload(texture)
    view_layer = importlib.reload(view_layer)
    view_layer_aovs = importlib.reload(view_layer_aovs)
    volume = importlib.reload(volume)
    world = importlib.reload(world)
    lol = importlib.reload(lol)
    render = importlib.reload(render)

classes = (
    addon_preferences.LuxCoreAddonPreferences,
    blender_object.LUXCORE_OBJECT_PT_object,
    blender_hair_curves.LUXCORE_DATA_PT_curve_hair,
    camera.LUXCORE_CAMERA_PT_presets,
    camera.LUXCORE_SAFE_AREAS_PT_presets,
    camera.LUXCORE_CAMERA_PT_lens,
    camera.LUXCORE_CAMERA_PT_clipping_plane,
    camera.LUXCORE_CAMERA_PT_depth_of_field,
    camera.LUXCORE_CAMERA_PT_bokeh,
    camera.LUXCORE_CAMERA_PT_motion_blur,
    camera.LUXCORE_CAMERA_PT_image_pipeline,
    camera.LUXCORE_CAMERA_PT_image_pipeline_tonemapper,
    camera.LUXCORE_CAMERA_PT_image_pipeline_bloom,
    camera.LUXCORE_CAMERA_PT_image_pipeline_mist,
    camera.LUXCORE_CAMERA_PT_image_pipeline_vignetting,
    camera.LUXCORE_CAMERA_PT_image_pipeline_color_aberration,
    camera.LUXCORE_CAMERA_PT_image_pipeline_background_image,
    camera.LUXCORE_CAMERA_PT_image_pipeline_white_balance,
    camera.LUXCORE_CAMERA_PT_image_pipeline_camera_response_function,
    camera.LUXCORE_CAMERA_PT_image_pipeline_color_LUT,
    camera.LUXCORE_CAMERA_PT_image_pipeline_contour_lines,
    camera.LUXCORE_CAMERA_PT_volume,
    image_tools.LUXCORE_IMAGE_PT_display,
    image_tools.LUXCORE_IMAGE_PT_denoiser,
    image_tools.LUXCORE_IMAGE_PT_statistics,
    light.LUXCORE_LIGHT_PT_context_light,
    light.LUXCORE_LIGHT_PT_volume,
    light.LUXCORE_LIGHT_PT_performance,
    light.LUXCORE_LIGHT_PT_visibility,
    light.LUXCORE_LIGHT_PT_spot,
    light.LUXCORE_LIGHT_PT_ies_light,
    light.LUXCORE_LIGHT_PT_nodes,
    light.LUXCORE_LIGHT_PT_cycles_nodes,
    material.LUXCORE_PT_context_material,
    material.LUXCORE_PT_material_presets,
    material.LUXCORE_PT_material_preview,
    material.LUXCORE_PT_material_settings,
    particle.LUXCORE_HAIR_PT_hair,
    particle.LUXCORE_PARTICLE_PT_textures,
    scene_lightgroups.LUXCORE_SCENE_PT_lightgroups,
    scene_units.LUXCORE_PT_unit_advanced,
    view_layer.LUXCORE_VIEWLAYER_PT_layer,
    view_layer.LUXCORE_VIEWLAYER_PT_override,
    view_layer_aovs.LUXCORE_RENDERLAYER_PT_aovs,
    view_layer_aovs.LUXCORE_RENDERLAYER_PT_aovs_basic,
    view_layer_aovs.LUXCORE_RENDERLAYER_PT_aovs_material_object,
    view_layer_aovs.LUXCORE_RENDERLAYER_PT_aovs_light,
    view_layer_aovs.LUXCORE_RENDERLAYER_PT_aovs_shadow,
    view_layer_aovs.LUXCORE_RENDERLAYER_PT_aovs_geometry,
    view_layer_aovs.LUXCORE_RENDERLAYER_PT_aovs_render,
    world.LUXCORE_PT_context_world,
    world.LUXCORE_WORLD_PT_sky2,
    world.LUXCORE_WORLD_PT_infinite,
    world.LUXCORE_WORLD_PT_volume,
    world.LUXCORE_WORLD_PT_performance,
    world.LUXCORE_WORLD_PT_visibility,
)


def register():
    lol.register()
    render.register()

    blender_object.register()
    camera.register()
    light.register()
    material.register()
    node_editor.register()
    output.register()
    particle.register()
    physics.register()
    texture.register()
    volume.register()
    world.register()

    for cls in classes:
        register_class(cls)


def unregister():
    lol.unregister()
    render.unregister()

    blender_object.unregister()
    camera.unregister()
    light.unregister()
    material.unregister()
    node_editor.unregister()
    output.unregister()
    particle.unregister()
    physics.unregister()
    texture.unregister()
    volume.unregister()
    world.unregister()

    for cls in classes:
        unregister_class(cls)
