from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from . import icons


class LUXCORE_RENDER_PT_photongi(RenderButtonsPanel, Panel):
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
        engine_is_bidir = context.scene.luxcore.config.engine == "BIDIR"

        if engine_is_bidir:
            layout.label(text="Not supported by Bidir", icon=icons.INFO)

        if not photongi.indirect_enabled and not photongi.caustic_enabled:
            layout.label(text="All caches disabled", icon=icons.WARNING)

        col = layout.column()
        col.active = not engine_is_bidir

        row = col.row(align=True)
        row.prop(photongi, "photon_maxcount")
        row.prop(photongi, "photon_maxdepth")

        sub = col.column(align=True)
        sub.prop(photongi, "indirect_enabled")
        sub = sub.column(align=True)
        sub.active = photongi.indirect_enabled
        sub.prop(photongi, "indirect_maxsize")
        sub.prop(photongi, "indirect_usagethresholdscale")
        sub.prop(photongi, "indirect_normalangle")
        sub.prop(photongi, "indirect_glossinessusagethreshold")
        row = sub.row()
        row.prop(photongi, "indirect_lookup_radius_auto")
        if not photongi.indirect_lookup_radius_auto:
            row.prop(photongi, "indirect_lookup_radius")

        sub = col.column(align=True)
        sub.prop(photongi, "caustic_enabled")
        sub = sub.column(align=True)
        sub.active = photongi.caustic_enabled
        row = sub.row(align=True)
        row.prop(photongi, "caustic_maxsize")
        row = sub.row(align=True)
        row.prop(photongi, "caustic_lookup_radius")
        row.prop(photongi, "caustic_lookup_maxcount")
        row = sub.row(align=True)
        row.prop(photongi, "caustic_normalangle")
        row = sub.row(align=False)
        row.prop(photongi, "caustic_merge_enabled")
        subrow = row.row(align=False)
        subrow.active = photongi.caustic_merge_enabled
        subrow.prop(photongi, "caustic_merge_radius_scale")

        col.prop(photongi, "debug")
        if ((photongi.debug == "showindirect" or photongi.debug == "showindirectpathmix")
                and not photongi.indirect_enabled) or (
                photongi.debug == "showcaustic" and not photongi.caustic_enabled):
            col.label(text="Can't show this cache (disabled)", icon=icons.WARNING)
