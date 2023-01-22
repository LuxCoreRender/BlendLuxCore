import bpy
from bpy.types import Panel
from . import icons
from .icons import icon_manager

from bl_ui.properties_particle import ParticleButtonsPanel
from .. import utils

def compatible_panels():
     panels = [
         "PARTICLE_PT_physics",
         "PARTICLE_PT_physics_fluid_advanced",
         "PARTICLE_PT_physics_fluid_springs",
         "PARTICLE_PT_physics_fluid_springs_viscoelastic",
         "PARTICLE_PT_physics_fluid_springs_advanced",
         "PARTICLE_PT_physics_boids_movement",
         "PARTICLE_PT_physics_boids_battle",
         "PARTICLE_PT_physics_boids_misc",
         "PARTICLE_PT_physics_relations",
         "PARTICLE_PT_physics_fluid_interaction",
         "PARTICLE_PT_physics_deflection",
         "PARTICLE_PT_physics_forces",
         "PARTICLE_PT_physics_integration",         
         "PARTICLE_PT_hair_dynamics",
         "PARTICLE_PT_hair_dynamics_structure",
         "PARTICLE_PT_hair_dynamics_volume",
         "PARTICLE_PT_emission",
         "PARTICLE_PT_emission_source",
         "PARTICLE_PT_boidbrain",
         "PARTICLE_PT_cache",
         "PARTICLE_PT_draw",
         "PARTICLE_PT_velocity",
         "PARTICLE_PT_field_weights",
         "PARTICLE_PT_force_fields",
         "PARTICLE_PT_force_fields_type1",
         "PARTICLE_PT_force_fields_type2",
         "PARTICLE_PT_force_fields_type1_falloff",
         "PARTICLE_PT_force_fields_type2_falloff",
         "PARTICLE_PT_vertexgroups",
         "PARTICLE_PT_children",
         "PARTICLE_PT_children_parting",
         "PARTICLE_PT_children_clumping",
         "PARTICLE_PT_children_clumping_noise",
         "PARTICLE_PT_children_roughness",
         "PARTICLE_PT_children_kink",
         "PARTICLE_PT_render",
         "PARTICLE_PT_render_extra",
         "PARTICLE_PT_render_path",
         "PARTICLE_PT_render_path_timing",
         "PARTICLE_PT_render_object",
         "PARTICLE_PT_render_collection",
         "PARTICLE_PT_render_collection_use_count",
         "PARTICLE_PT_rotation",
         "PARTICLE_PT_rotation_angular_velocity",
         "PARTICLE_PT_context_particles",
         #"PARTICLE_PT_textures",
         "PARTICLE_PT_hair_shape",
         "PARTICLE_PT_custom_props",
     ]
     types = bpy.types
     return [getattr(types, p) for p in panels if hasattr(types, p)]

class LUXCORE_HAIR_PT_hair(ParticleButtonsPanel, Panel):
    bl_label = "LuxCore Hair Settings"
    COMPAT_ENGINES = {"LUXCORE"}
    bl_order = 10
    
    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        if psys is None:
            return False
        if psys.settings is None:
            return False
        is_hair = psys.settings.type == "HAIR"
        is_path = psys.settings.render_type == "PATH"
        engine = context.scene.render.engine
        return is_hair and is_path and engine == "LUXCORE"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

    def draw(self, context):
        layout = self.layout
        settings = context.particle_settings.luxcore.hair

        layout.use_property_split = True
        layout.use_property_decorate = False      

        # Note: we can always assume that obj.data has the attribute uv_textures,
        # because objects that don't have it can't have a particle system in Blender.
        # We can also assume that obj.data exists, because otherwise this panel is not visible.
        obj = context.object

        layout.prop(settings, "hair_size")

        col = layout.column(align=True)
        col.prop(settings, "root_width")
        col.prop(settings, "tip_width")
        col.prop(settings, "width_offset")

        layout.prop(settings, "tesseltype")

        if "adaptive" in settings.tesseltype:
            col = layout.column(align=True)
            col.prop(settings, "adaptive_maxdepth")
            col.prop(settings, "adaptive_error")

        if settings.tesseltype.startswith("solid"):
            layout.prop(settings, "solid_sidecount")

            col = layout.column(align=True)
            col.prop(settings, "solid_capbottom")
            col.prop(settings, "solid_captop")

        layout.prop(settings, "copy_uv_coords")

        # UV map selection
        box = layout.box()
        box.enabled = settings.copy_uv_coords or settings.export_color == "uv_texture_map"
        col = box.column()
        col.prop(settings, "use_active_uv_map")

        if settings.use_active_uv_map:
            if obj.data.uv_layers:
                active_uv = utils.find_active_uv(obj.data.uv_layers)
                if active_uv:
                    row = col.row(align=True)
                    row.label(text="UV Map")
                    row.label(text=active_uv.name, icon="GROUP_UVS")
        else:
            col.prop_search(settings, "uv_map_name",
                            obj.data, "uv_layers",
                            icon="GROUP_UVS")

        if not obj.data.uv_layers:
            row = col.row()
            row.label(text="No UV map", icon=icons.WARNING)
            row.operator("mesh.uv_texture_add", icon=icons.ADD)

        # Vertex color settings
        box = layout.box()
        box.prop(settings, "export_color")

        if settings.export_color == "vertex_color":
            col = box.column(align=True)
            col.prop(settings, "use_active_vertex_color_layer")

            if settings.use_active_vertex_color_layer:
                if obj.data.vertex_colors:
                    active_vcol_layer = utils.find_active_vertex_color_layer(obj.data.vertex_colors)
                    if active_vcol_layer:
                        row = col.row(align=True)
                        row.label(text="Vertex Colors")
                        row.label(text=active_vcol_layer.name, icon="GROUP_VCOL")
            else:
                col.prop_search(settings, "vertex_color_layer_name",
                                obj.data, "vertex_colors",
                                icon="GROUP_VCOL", text="Vertex Colors")

            if not obj.data.vertex_colors:
                row = col.row()
                row.label(text="No Vertex Colors", icon=icons.WARNING)
                row.operator("mesh.vertex_color_add", icon=icons.ADD)

        elif settings.export_color == "uv_texture_map":
            box.template_ID(settings, "image", open="image.open")
            if settings.image:
                box.prop(settings, "gamma")
            settings.image_user.draw(box, context.scene)

        col = box.column(align=True)
        col.prop(settings, "root_color")
        col.prop(settings, "tip_color")

        layout.prop(settings, "instancing")


class LUXCORE_PARTICLE_PT_textures(ParticleButtonsPanel, Panel):
    bl_label = "Textures"
    bl_context = "particle"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        if psys is None:
            return False
        if psys.settings is None:
            return False
        return engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system
        part = psys.settings

        row = layout.row()
        row.template_list("TEXTURE_UL_texslots", "", part, "texture_slots", part, "active_texture_index", rows=2)

        col = row.column(align=True)
        col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
        col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
        col.menu("TEXTURE_MT_specials", icon='DOWNARROW_HLT', text="")

        if not part.active_texture:
            layout.template_ID(part, "active_texture", new="texture.new")
        else:
            slot = part.texture_slots[part.active_texture_index]
            layout.template_ID(slot, "texture", new="texture.new")

            row = layout.row()
            op = row.operator("luxcore.switch_space_data_context", text="Show Texture Settings", icon="UI")
            op.target = "TEXTURE"

def register():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.add("LUXCORE")        


def unregister():
    for panel in compatible_panels():
        panel.COMPAT_ENGINES.remove("LUXCORE")
