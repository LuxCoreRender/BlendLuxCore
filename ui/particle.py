from bl_ui.properties_particle import ParticleButtonsPanel
from bpy.types import Panel


class LUXCORE_HAIR_PT_hair(ParticleButtonsPanel, Panel):
    bl_label = "LuxCore Hair Settings"
    COMPAT_ENGINES = {"LUXCORE"}
    
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
        
    def draw(self, context):
        layout = self.layout
        settings = context.particle_settings.luxcore.hair

        layout.prop(settings, "hair_size")

        row = layout.row(align=True)
        row.prop(settings, "root_width")
        row.prop(settings, "tip_width")        
        row.prop(settings, "width_offset")

        layout.prop(settings, "tesseltype")

        if "adaptive" in settings.tesseltype:
            row = layout.row(align=True)
            row.prop(settings, "adaptive_maxdepth")
            row.prop(settings, "adaptive_error")

        if settings.tesseltype.startswith("solid"):
            layout.prop(settings, "solid_sidecount")

            row = layout.row()
            row.prop(settings, "solid_capbottom")            
            row.prop(settings, "solid_captop")

        layout.prop(settings, "export_color")


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
