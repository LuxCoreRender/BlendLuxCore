from bl_ui.properties_particle import ParticleButtonsPanel
from bpy.types import Panel

class LuxCoreHairSettings(ParticleButtonsPanel, Panel):
    bl_label = "LuxCore Hair Settings"
    COMPAT_ENGINES = {"LUXCORE"}
    
    @classmethod
    def poll(cls, context):        
        psys = context.particle_system
        engine = context.scene.render.engine
        if psys is None:
            return False
        if psys.settings is None:
            return False
        return psys.settings.type == "HAIR" and (engine == "LUXCORE")
        
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
