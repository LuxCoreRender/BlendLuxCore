from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel


class LUXCORE_RENDER_PT_config(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore PhotonGI Cache"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        self.layout.prop(context.scene.luxcore.config.photongi, "enabled", text="")

    def draw(self, context):
        layout = self.layout
        photongi = context.scene.luxcore.config.photongi
        layout.active = photongi.enabled

        row = layout.row(align=True)
        row.prop(photongi, "photon_maxcount")
        row.prop(photongi, "photon_maxdepth")

        col = layout.column()
        col.prop(photongi, "indirect_enabled")
        row = col.row(align=True)
        row.active = photongi.indirect_enabled
        row.prop(photongi, "indirect_maxsize")
        row.prop(photongi, "indirect_lookup_radius")

        col = layout.column()
        col.prop(photongi, "caustic_enabled")
        row = col.row(align=True)
        row.active = photongi.caustic_enabled
        row.prop(photongi, "caustic_maxsize")
        row.prop(photongi, "caustic_lookup_radius")

        layout.prop(photongi, "debug")
