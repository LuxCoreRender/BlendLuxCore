from platform import system
from os import environ

# Fix problem of OpenMP calling a trap about two libraries loading because blender's
# openmp lib uses @loader_path and zip does not preserve symbolic links (so can't
# spoof loader_path with symlinks)
if system() == "Darwin":
    environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


from bpy.utils import register_class, unregister_class
from . import (
    camera, debug, general, imagepipeline, ior_presets, keymaps, light, lightgroups, manual_compatibility,
    material, multi_image_import, node_editor, node_tree_presets, pointer_node, pyluxcoretools,
    render, render_settings_helper, texture, world, lol,
)

classes = (
    camera.LUXCORE_OT_camera_new_volume_node_tree,
    camera.LUXCORE_OT_camera_unlink_volume_node_tree,
    camera.LUXCORE_OT_camera_set_volume_node_tree,
    camera.LUXCORE_VOLUME_MT_camera_select_volume_node_tree,
    camera.LUXCORE_OT_camera_show_volume_node_tree,
    debug.LUXCORE_OT_toggle_debug_options,
    debug.LUXCORE_OT_debug_restart,
    general.LUXCORE_OT_use_cycles_settings,
    general.LUXCORE_OT_use_cycles_nodes_everywhere,
    general.LUXCORE_OT_errorlog_clear,
    general.LUXCORE_OT_switch_texture_context,
    general.LUXCORE_OT_switch_space_data_context,
    general.LUXCORE_OT_switch_to_camera_settings,
    general.LUXCORE_OT_set_suggested_clamping_value,
    general.LUXCORE_OT_update_opencl_devices,
    general.LUXCORE_OT_add_node,
    general.LUXCORE_OT_attach_sun_to_sky,
    general.LUXCORE_OT_copy_error_to_clipboard,
    general.LUXCORE_OT_open_website,
    general.LUXCORE_OT_open_website_popup,
    general.LUXCORE_OT_select_object,
    imagepipeline.LUXCORE_OT_select_crf,
    imagepipeline.LUXCORE_OT_set_raw_view_transform,
    ior_presets.LUXCORE_OT_ior_preset_names,
    ior_presets.LUXCORE_OT_ior_preset_values,
    light.LUXCORE_OT_light_new_volume_node_tree,
    light.LUXCORE_OT_light_unlink_volume_node_tree,
    light.LUXCORE_OT_light_set_volume_node_tree,
    light.LUXCORE_VOLUME_MT_light_select_volume_node_tree,
    light.LUXCORE_OT_light_show_volume_node_tree,
    lightgroups.LUXCORE_OT_add_lightgroup,
    lightgroups.LUXCORE_OT_remove_lightgroup,
    lightgroups.LUXCORE_OT_select_objects_in_lightgroup,
    lightgroups.LUXCORE_OT_create_lightgroup_nodes,
    manual_compatibility.LUXCORE_OT_convert_to_v23,
    material.LUXCORE_OT_material_new,
    material.LUXCORE_OT_material_unlink,
    material.LUXCORE_OT_material_copy,
    material.LUXCORE_OT_material_set,
    material.LUXCORE_MT_material_select,
    material.LUXCORE_OT_material_select,
    material.LUXCORE_OT_material_show_nodetree,
    material.LUXCORE_OT_mat_nodetree_new,
    material.LUXCORE_OT_set_mat_node_tree,
    material.LUXCORE_MATERIAL_MT_node_tree,
    multi_image_import.LUXCORE_OT_import_multiple_images,
    node_editor.LUXCORE_OT_node_editor_viewer,
    node_editor.LUXCORE_OT_mute_node,
    node_editor.LUXCORE_OT_node_editor_add_image,
    node_tree_presets.LUXCORE_OT_preset_material,
    node_tree_presets.LUXCORE_MATERIAL_MT_node_tree_preset,
    pointer_node.LUXCORE_OT_pointer_unlink_node_tree,
    pointer_node.LUXCORE_OT_pointer_set_node_tree,
    pointer_node.LUXCORE_MT_pointer_select_node_tree,
    pointer_node.LUXCORE_OT_pointer_show_node_tree,
    pyluxcoretools.LUXCORE_OT_install_pyside,
    pyluxcoretools.LUXCORE_OT_start_pyluxcoretools,
    render.LUXCORE_OT_request_denoiser_refresh,
    render.LUXCORE_OT_request_display_refresh,
    render.LUXCORE_OT_toggle_pause,
    render.LUXCORE_OT_stop_render,
    render_settings_helper.LUXCORE_OT_render_settings_helper,
    texture.LUXCORE_OT_texture_show_nodetree,
    texture.LUXCORE_OT_tex_nodetree_new,
    texture.LUXCORE_OT_texture_unlink,
    texture.LUXCORE_OT_texture_set_node_tree,
    texture.LUXCORE_MT_texture_select_node_tree,
    world.LUXCORE_OT_world_new_volume_node_tree,
    world.LUXCORE_OT_world_unlink_volume_node_tree,
    world.LUXCORE_OT_world_set_volume_node_tree,
    world.LUXCORE_VOLUME_MT_world_select_volume_node_tree,
    world.LUXCORE_OT_world_show_volume_node_tree,
    world.LUXCORE_OT_world_set_ground_black,
    world.LUXCORE_OT_create_sun_hemi,
)

def register():
    lol.register()
    keymaps.register()

    for cls in classes:
        try:
            register_class(cls)
        except Exception as err:
            print("Warning: Cannot register", cls, err)

def unregister():
    lol.unregister()
    keymaps.unregister()

    for cls in classes:
        unregister_class(cls)
