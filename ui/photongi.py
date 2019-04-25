import os
from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from . import icons
from .. import utils


class LUXCORE_RENDER_PT_photongi(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore PhotonGI Cache"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        self.layout.prop(context.scene.luxcore.config.photongi, "enabled", text="")

    def draw(self, context):
        photongi = context.scene.luxcore.config.photongi
        layout = self.layout
        layout.active = photongi.enabled
        engine_is_bidir = context.scene.luxcore.config.engine == "BIDIR"

        if engine_is_bidir:
            layout.label(text="Not supported by Bidir", icon=icons.INFO)

        if not photongi.indirect_enabled and not photongi.caustic_enabled:
            layout.label(text="All caches disabled", icon=icons.WARNING)

        col = layout.column()
        col.active = not engine_is_bidir

        sub = col.column(align=True)
        sub.prop(photongi, "photon_maxcount")
        sub.prop(photongi, "photon_maxdepth")

        sub = col.column(align=True)
        sub.prop(photongi, "indirect_enabled")
        sub = sub.column(align=True)
        sub.active = photongi.indirect_enabled
        row = sub.row()
        row.prop(photongi, "indirect_haltthreshold_preset")
        if photongi.indirect_haltthreshold_preset == "custom":
            row.prop(photongi, "indirect_haltthreshold_custom")
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

        file_abspath = utils.get_abspath(photongi.file_path, library=context.scene.library)
        file_exists = os.path.isfile(file_abspath)

        if not file_abspath:
            cache_status = "Cache file will not be saved"
        elif photongi.save_or_overwrite:
            if file_exists:
                cache_status = "Cache file exists, but will be overwritten"
            else:
                cache_status = "Cache file will be saved"
        else:
            if file_exists:
                cache_status = "Will use cache from file"
            else:
                cache_status = "No cache file available"

        col = layout.column()
        col.prop(photongi, "save_or_overwrite",
                 text="Compute and overwrite" if file_exists else "Compute and save")
        col.prop(photongi, "file_path", text="")
        col.label(cache_status)
