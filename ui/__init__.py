import bpy


# Note: this is an include list
# We could also use an exclude list, may be shorter
def compatible_panels():
    panels = [
        # Render panels
        "RENDER_PT_render",
        "RENDER_PT_output",
        "RENDER_PT_encoding",
        "RENDER_PT_dimensions",
        "RENDER_PT_stamp",

        # Data panels
        # Lamp
        "DATA_PT_context_lamp",
        # Mesh
        "DATA_PT_context_mesh",
        "DATA_PT_normals",
        "DATA_PT_texture_space",
        "DATA_PT_vertex_groups",
        "DATA_PT_shape_keys",
        "DATA_PT_uv_texture",
        "DATA_PT_vertex_colors",
        "DATA_PT_customdata",  # TODO do we really support this?
        "DATA_PT_custom_props_mesh",
        # Speaker
        "DATA_PT_context_speaker",
        "DATA_PT_speaker",
        "DATA_PT_distance",
        "DATA_PT_cone",
        "DATA_PT_custom_props_speaker",
        # Camera
        "DATA_PT_camera",
        "DATA_PT_camera_display",
        "DATA_PT_camera_safe_areas",
        "DATA_PT_camera_steroscopy",        
        "DATA_PT_custom_props_camera",        

        # World panels
        "WORLD_PT_context_world",
        "WORLD_PT_custom_props",

        # Scene panels
        # TODO: can we support SCENE_PT_scene (background scenes)?
        "SCENE_PT_unit",
        "SCENE_PT_keying_sets",
        "SCENE_PT_keying_set_paths",
        "SCENE_PT_color_management",
        "SCENE_PT_audio",
        "SCENE_PT_physics",
        "SCENE_PT_rigid_body_world",
        "SCENE_PT_rigid_body_cache",
        "SCENE_PT_rigid_body_field_weights",
        "SCENE_PT_custom_props",

        # Texture panels
        # Used only for particles/brushes
        "TEXTURE_PT_preview",
        "TEXTURE_PT_colors",
        "TEXTURE_PT_influence",
        "TEXTURE_PT_mapping",
        # One panel per texture type
        "TEXTURE_PT_image",
        "TEXTURE_PT_image_mapping",
        "TEXTURE_PT_blend",
        "TEXTURE_PT_clouds",
        "TEXTURE_PT_distortednoise",
        "TEXTURE_PT_magic",
        "TEXTURE_PT_marble",
        "TEXTURE_PT_musgrave",
        "TEXTURE_PT_ocean",
        "TEXTURE_PT_pointdensity",
        "TEXTURE_PT_pointdensity_turbulence",
        "TEXTURE_PT_stucci",
        "TEXTURE_PT_voronoi",
        "TEXTURE_PT_voxeldata",
        "TEXTURE_PT_wood",

        # Particles
        "PARTICLE_PT_physics",
        "PARTICLE_PT_hair_dynamics",
        "PARTICLE_MT_specials",
        "PARTICLE_PT_emission",
        "PARTICLE_PT_boidbrain",
        "PARTICLE_PT_cache",
        "PARTICLE_PT_draw",
        "PARTICLE_PT_velocity",
        "PARTICLE_PT_force_fields",
        "PARTICLE_PT_vertexgroups",
        "PARTICLE_PT_children",
        "PARTICLE_MT_hair_dynamics_presets",
        "PARTICLE_PT_render",
        "PARTICLE_PT_rotation",
        "PARTICLE_PT_context_particles",
        "PARTICLE_PT_field_weights",
        "PARTICLE_PT_custom_props",

        # Physics
        # Common
        "PHYSICS_PT_add",
        # Dynamic paint
        "PHYSICS_PT_dynamic_paint",
        "PHYSICS_PT_dp_advanced_canvas",
        "PHYSICS_PT_dp_canvas_output",
        "PHYSICS_PT_dp_canvas_initial_color",
        "PHYSICS_PT_dp_effects",
        "PHYSICS_PT_dp_cache",
        "PHYSICS_PT_dp_brush_source",
        "PHYSICS_PT_dp_brush_velocity",
        "PHYSICS_PT_dp_brush_wave",
        # Forcefields
        "PHYSICS_PT_field",
        # Collisions
        "PHYSICS_PT_collision",
        # Fluid
        "PHYSICS_PT_fluid",
        "PHYSICS_PT_domain_gravity",
        "PHYSICS_PT_domain_boundary",
        "PHYSICS_PT_domain_particles",
        # Rigidbody
        "PHYSICS_PT_rigid_body",
        "PHYSICS_PT_rigid_body_dynamics",
        "PHYSICS_PT_rigid_body_collisions",
        # Rigidbody constraints
        "PHYSICS_PT_rigid_body_constraint",
        # Softbody
        "PHYSICS_PT_softbody",
        "PHYSICS_PT_softbody_cache",
        "PHYSICS_PT_softbody_goal",
        "PHYSICS_PT_softbody_edge",
        "PHYSICS_PT_softbody_collision",
        "PHYSICS_PT_softbody_solver",
        "PHYSICS_PT_softbody_field_weights",
        # Cloth
        "PHYSICS_PT_cloth",
        "PHYSICS_PT_cloth_cache",
        "PHYSICS_PT_cloth_collision",
        "PHYSICS_PT_cloth_stiffness",
        "PHYSICS_PT_cloth_sewing",
        "PHYSICS_PT_cloth_field_weights",
        # Smoke
        "PHYSICS_PT_smoke",
        "PHYSICS_PT_smoke_groups",
        "PHYSICS_PT_smoke_cache",
        "PHYSICS_PT_smoke_highres",
        "PHYSICS_PT_smoke_field_weights",
    ]
    types = bpy.types
    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")

    from . import render, units
    render.register()
    units.register()


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")

    from . import render, units
    render.unregister()
    units.unregister()
