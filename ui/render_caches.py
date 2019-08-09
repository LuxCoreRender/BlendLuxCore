import os
from bl_ui.properties_render import RenderButtonsPanel
from ..operators.config import LUXCORE_OT_config_set_dlsc
from bpy.types import Panel
from . import icons
from .. import utils


class LUXCORE_RENDER_PT_caches(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "LuxCore Caches"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 11

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        pass


class LUXCORE_RENDER_PT_caches_photongi(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "PhotonGI Cache"
    bl_parent_id = "LUXCORE_RENDER_PT_caches"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        self.layout.prop(context.scene.luxcore.config.photongi, "enabled", text="")

    def draw(self, context):
        photongi = context.scene.luxcore.config.photongi
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        engine_is_bidir = context.scene.luxcore.config.engine == "BIDIR"
        layout.enabled = photongi.enabled and not engine_is_bidir

        if engine_is_bidir:
            layout.label(text="Not supported by Bidir", icon=icons.INFO)

        if not photongi.indirect_enabled and not photongi.caustic_enabled:
            layout.label(text="All caches disabled", icon=icons.WARNING)

        col = layout.column(align=True)
        col.prop(photongi, "photon_maxcount")
        col.prop(photongi, "photon_maxdepth")

        col = layout.column(align=True)
        col.prop(photongi, "indirect_enabled")

        col = layout.column(align=True)
        col.enabled = photongi.indirect_enabled

        col = layout.column(align=True)
        col.prop(photongi, "indirect_haltthreshold_preset")
        if photongi.indirect_haltthreshold_preset == "custom":
            col.prop(photongi, "indirect_haltthreshold_custom")
        col.prop(photongi, "indirect_usagethresholdscale")
        col.prop(photongi, "indirect_normalangle")
        col.prop(photongi, "indirect_glossinessusagethreshold")
        col = layout.column(align=True)
        col.prop(photongi, "indirect_lookup_radius_auto")
        if not photongi.indirect_lookup_radius_auto:
            col.prop(photongi, "indirect_lookup_radius")

        col = layout.column(align=True)
        col.prop(photongi, "caustic_enabled")
        col = layout.column(align=True)
        col.enabled = photongi.caustic_enabled
        sub = col.column(align=True)
        sub.prop(photongi, "caustic_maxsize")
        sub = col.column(align=True)
        sub.prop(photongi, "caustic_lookup_radius")
        sub.prop(photongi, "caustic_lookup_maxcount")
        sub = col.column(align=True)
        sub.prop(photongi, "caustic_normalangle")
        sub = col.column(align=True)
        sub.prop(photongi, "caustic_merge_enabled")
        sub = col.column(align=True)
        sub.enabled = photongi.caustic_merge_enabled
        sub.prop(photongi, "caustic_merge_radius_scale")

        col = layout.column(align=True)
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

        col = layout.column(align=True)
        col.prop(photongi, "save_or_overwrite",
                 text="Compute and overwrite" if file_exists else "Compute and save")
        col.prop(photongi, "file_path", text="")
        col.label(text=cache_status)


class LUXCORE_RENDER_PT_caches_envlight(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Environment Light Cache"
    bl_parent_id = "LUXCORE_RENDER_PT_caches"
    lux_predecessor = "LUXCORE_RENDER_PT_caches_photongi"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        self.layout.prop(context.scene.luxcore.config.envlight_cache, "enabled", text="")

    def draw(self, context):
        envlight_cache = context.scene.luxcore.config.envlight_cache
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(envlight_cache, "map_width")
        layout.prop(envlight_cache, "samples")


class LUXCORE_RENDER_PT_caches_DLSC(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Direct Light Sampling Cache"
    bl_parent_id = "LUXCORE_RENDER_PT_caches"
    lux_predecessor = "LUXCORE_RENDER_PT_caches_envlight"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        dls_cache = context.scene.luxcore.config.dls_cache
        use_dlsc = context.scene.luxcore.config.light_strategy == 'DLS_CACHE'
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        if not context.scene.luxcore.config.light_strategy == 'DLS_CACHE':
            col.operator("luxcore.config_set_dlsc")
        else:
            col.label(text="DLS Cache can be disabled in Light Strategy Menu", icon=icons.INFO)
            col = layout.column(align=True)
            col.active = use_dlsc
            col.prop(dls_cache, "entry_radius_auto")
            if not dls_cache.entry_radius_auto:
                col.prop(dls_cache, "entry_radius")
            col.prop(dls_cache, "entry_warmupsamples")


class LUXCORE_RENDER_PT_caches_DLSC_advanced(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Advanced"
    bl_parent_id = "LUXCORE_RENDER_PT_caches_DLSC"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE" and context.scene.luxcore.config.light_strategy == 'DLS_CACHE'

    def draw(self, context):
        config = context.scene.luxcore.config
        dls_cache = config.dls_cache
        use_dlsc = context.scene.luxcore.config.light_strategy == 'DLS_CACHE'
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.active = use_dlsc

        col = layout.column(align=True)
        col.label(text="Entry Settings:")
        col.prop(dls_cache, "entry_normalangle")
        col.prop(dls_cache, "entry_maxpasses")
        col.prop(dls_cache, "entry_convergencethreshold")
        col.prop(dls_cache, "entry_volumes_enable")

        col = layout.column(align=True)
        col.label(text="General Cache Settings:")
        col.prop(dls_cache, "lightthreshold")
        col.prop(dls_cache, "targetcachehitratio")
        col.prop(dls_cache, "maxdepth")
        col.prop(dls_cache, "maxsamplescount")
