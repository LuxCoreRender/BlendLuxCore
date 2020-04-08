import bpy

# Note: The main LuxCore config UI is defined in ui/config.py
# Each of the other render panels is also defined in their
# own specific files in the ui/ folder.

def compatible_panels():
     panels = [
         # Physics
         # Common
         "PHYSICS_PT_add",      
         # Dynamic paint
         "PHYSICS_PT_dynamic_paint",
         "PHYSICS_PT_dynamic_paint_settings",
         "PHYSICS_PT_dp_surface_canvas",
         "PHYSICS_PT_dp_surface_canvas_paint_dry",
         "PHYSICS_PT_dp_surface_canvas_paint_dissolve",
         "PHYSICS_PT_dp_canvas_output",
         "PHYSICS_PT_dp_canvas_output_paintmaps",
         "PHYSICS_PT_dp_canvas_output_wetmaps",
         "PHYSICS_PT_dp_canvas_initial_color",
         "PHYSICS_PT_dp_effects",
         "PHYSICS_PT_dp_effects_spread",
         "PHYSICS_PT_dp_effects_drip",
         "PHYSICS_PT_dp_effects_drip_weights",
         "PHYSICS_PT_dp_effects_shrink",
         "PHYSICS_PT_dp_cache",
         "PHYSICS_PT_dp_brush_source",
         "PHYSICS_PT_dp_brush_source_color_ramp",
         "PHYSICS_PT_dp_brush_velocity",
         "PHYSICS_PT_dp_brush_velocity_color_ramp",
         "PHYSICS_PT_dp_brush_velocity_smudge",
         "PHYSICS_PT_dp_brush_wave",
         # Forcefields
         "PHYSICS_PT_field",
         "PHYSICS_PT_field_settings",
         "PHYSICS_PT_field_settings_kink",
         "PHYSICS_PT_field_settings_texture_select",
         "PHYSICS_PT_field_falloff",
         "PHYSICS_PT_field_falloff_angular",
         "PHYSICS_PT_field_falloff_radial",         
         # Collisions
         "PHYSICS_PT_collision",
         "PHYSICS_PT_collision_particle",
         "PHYSICS_PT_collision_softbody",
         # Rigidbody
         "PHYSICS_PT_rigid_body",
         "PHYSICS_PT_rigid_body_settings",
         "PHYSICS_PT_rigid_body_collisions",
         "PHYSICS_PT_rigid_body_collisions_surface",
         "PHYSICS_PT_rigid_body_collisions_sensitivity",
         "PHYSICS_PT_rigid_body_collisions_collections",
         "PHYSICS_PT_rigid_body_dynamics",
         "PHYSICS_PT_rigid_body_dynamics_deactivation",
         # Rigidbody constraints
         "PHYSICS_PT_rigid_body_constraint",
         "PHYSICS_PT_rigid_body_constraint_settings",
         "PHYSICS_PT_rigid_body_constraint_objects",
         "PHYSICS_PT_rigid_body_constraint_override_iterations",
         "PHYSICS_PT_rigid_body_constraint_limits",
         "PHYSICS_PT_rigid_body_constraint_limits_linear",
         "PHYSICS_PT_rigid_body_constraint_limits_angular",
         "PHYSICS_PT_rigid_body_constraint_motor",
         "PHYSICS_PT_rigid_body_constraint_motor_angular",
         "PHYSICS_PT_rigid_body_constraint_motor_linear",
         "PHYSICS_PT_rigid_body_constraint_springs",
         "PHYSICS_PT_rigid_body_constraint_springs_angular",
         "PHYSICS_PT_rigid_body_constraint_springs_linear",
         # Softbody
         "PHYSICS_PT_softbody",
         "PHYSICS_PT_softbody_object",
         "PHYSICS_PT_softbody_simulation",
         "PHYSICS_PT_softbody_cache",
         "PHYSICS_PT_softbody_goal",
         "PHYSICS_PT_softbody_goal_strengths",
         "PHYSICS_PT_softbody_goal_settings",
         "PHYSICS_PT_softbody_edge",
         "PHYSICS_PT_softbody_edge_aerodynamics",
         "PHYSICS_PT_softbody_edge_stiffness",
         "PHYSICS_PT_softbody_collision",
         "PHYSICS_PT_softbody_solver",
         "PHYSICS_PT_softbody_solver_diagnostics",
         "PHYSICS_PT_softbody_solver_helpers",
         "PHYSICS_PT_softbody_field_weights",
         # Cloth
         "PHYSICS_PT_cloth",
         "PHYSICS_PT_cloth_physical_properties",
         "PHYSICS_PT_cloth_stiffness",
         "PHYSICS_PT_cloth_damping",
         "PHYSICS_PT_cloth_cache",
         "PHYSICS_PT_cloth_shape",
         "PHYSICS_PT_cloth_collision",
         "PHYSICS_PT_cloth_object_collision",
         "PHYSICS_PT_cloth_self_collision",
         "PHYSICS_PT_cloth_property_weights",
         "PHYSICS_PT_cloth_field_weights",
         "PHYSICS_PT_cloth_internal_springs",
         "PHYSICS_PT_cloth_pressure",
         # Old fluid panels (up to Blender 2.81)
         "PHYSICS_PT_fluid_flow",
         "PHYSICS_PT_fluid_settings",
         "PHYSICS_PT_fluid_particle_cache",
         "PHYSICS_PT_domain_bake"
         "PHYSICS_PT_domain_gravity",
         "PHYSICS_PT_domain_viscosity",
         "PHYSICS_PT_domain_boundary",
         "PHYSICS_PT_domain_particles",
         # New smoke/fluid panels since Blender 2.82
         "PHYSICS_PT_fluid",
         "PHYSICS_PT_settings",
         "PHYSICS_PT_borders",
         "PHYSICS_PT_smoke",
         "PHYSICS_PT_smoke_dissolve",
         "PHYSICS_PT_fire",
         "PHYSICS_PT_liquid",
         "PHYSICS_PT_flow_source",
         "PHYSICS_PT_flow_initial_velocity",
         "PHYSICS_PT_flow_texture",
         "PHYSICS_PT_adaptive_domain",
         "PHYSICS_PT_noise",
         "PHYSICS_PT_mesh",
         "PHYSICS_PT_particles",
         "PHYSICS_PT_diffusion",
         "PHYSICS_PT_guide",
         "PHYSICS_PT_collections",
         "PHYSICS_PT_cache",
         "PHYSICS_PT_export",
         "PHYSICS_PT_field_weights",
     ]
     types = bpy.types
     return [getattr(types, p) for p in panels if hasattr(types, p)]

     
def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")        


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")
