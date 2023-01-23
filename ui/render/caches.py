import os
import math
from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from .. import icons
from ..icons import icon_manager
from ... import utils


def draw_persistent_file_ui(context, layout, settings):
    layout.use_property_split = True
    layout.use_property_decorate = False

    engine_is_bidir = context.scene.luxcore.config.engine == "BIDIR"
    layout.active = settings.enabled and not engine_is_bidir

    file_abspath = utils.get_abspath(settings.file_path, library=context.scene.library)
    file_exists = os.path.isfile(file_abspath)

    if not file_abspath:
        cache_status = "Cache file will not be saved"
    elif settings.save_or_overwrite:
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
    col.prop(settings, "save_or_overwrite",
             text="Compute and overwrite" if file_exists else "Compute and save")
    col.prop(settings, "file_path", text="")
    col.label(text=cache_status)


class LUXCORE_RENDER_PT_caches(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Caches"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 80

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value= icon_manager.get_icon_id("logotype"))

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon_value=icon_manager.get_icon_id("logotype"))

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

        layout.active = photongi.enabled

        if photongi.enabled and not photongi.indirect_enabled and not photongi.caustic_enabled:
            layout.label(text="All caches disabled", icon=icons.WARNING)

        col = layout.column(align=True)
        col.prop(photongi, "photon_maxcount")
        col.prop(photongi, "photon_maxdepth")
        col.prop(photongi, "glossinessusagethreshold")

        col = layout.column(align=True)
        col.prop(photongi, "debug")
        if ((photongi.debug == "showindirect" or photongi.debug == "showindirectpathmix")
                and not photongi.indirect_enabled) or (
                photongi.debug == "showcaustic" and not photongi.caustic_enabled):
            col.label(text="Can't show this cache (disabled)", icon=icons.WARNING)


class LUXCORE_RENDER_PT_caches_photongi_indirect(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = " "  # Label is drawn manually in draw_header() so we can make it inactive
    bl_parent_id = "LUXCORE_RENDER_PT_caches_photongi"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        self.layout.active = context.scene.luxcore.config.photongi.enabled and context.scene.luxcore.config.engine == "PATH"
        row = self.layout.row(align=True)
        row.prop(context.scene.luxcore.config.photongi, "indirect_enabled", text="")
        row.label(text="Indirect Light Cache")

    def draw(self, context):
        photongi = context.scene.luxcore.config.photongi
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        engine_is_bidir = context.scene.luxcore.config.engine == "BIDIR"
        if engine_is_bidir:
            layout.label(text="Not supported by Bidir", icon=icons.INFO)

        layout.active = photongi.enabled and photongi.indirect_enabled and not engine_is_bidir

        col = layout.column(align=True)
        col.prop(photongi, "indirect_haltthreshold_preset")
        if photongi.indirect_haltthreshold_preset == "custom":
            col.prop(photongi, "indirect_haltthreshold_custom")
        col.prop(photongi, "indirect_usagethresholdscale")
        col.prop(photongi, "indirect_normalangle")
        col = layout.column(align=True)
        col.prop(photongi, "indirect_lookup_radius_auto")
        if not photongi.indirect_lookup_radius_auto:
            col.prop(photongi, "indirect_lookup_radius")


class LUXCORE_RENDER_PT_caches_photongi_caustic(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = " "  # Label is drawn manually in draw_header() so we can make it inactive
    bl_parent_id = "LUXCORE_RENDER_PT_caches_photongi"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        self.layout.active = context.scene.luxcore.config.photongi.enabled
        row = self.layout.row(align=True)
        row.prop(context.scene.luxcore.config.photongi, "caustic_enabled", text="")
        row.label(text="Caustic Light Cache")

    def draw(self, context):
        photongi = context.scene.luxcore.config.photongi
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.active = photongi.enabled and photongi.caustic_enabled

        col = layout.column(align=True)
        col.enabled = photongi.caustic_enabled
        sub = col.column(align=True)
        sub.prop(photongi, "caustic_maxsize")
        sub.prop(photongi, "caustic_lookup_radius")
        sub.prop(photongi, "caustic_normalangle")
        sub.prop(photongi, "caustic_periodic_update")
        sub = col.column(align=True)
        sub.enabled = photongi.caustic_periodic_update
        sub.prop(photongi, "caustic_updatespp")
        sub.prop(photongi, "caustic_updatespp_radiusreduction")
        sub.prop(photongi, "caustic_updatespp_minradius")

        radius = photongi.caustic_lookup_radius
        minradius = photongi.caustic_updatespp_minradius

        if minradius >= radius:
            sub.label(text="Radius reduction disabled (min radius >= radius)")
        else:
            radius_multiplier = photongi.caustic_updatespp_radiusreduction / 100
            steps = (math.log(minradius / radius) / math.log(radius_multiplier))
            steps = math.ceil(steps)
            sub.label(text=f"Min radius reached after {steps} steps ({steps * photongi.caustic_updatespp} samples)")


class LUXCORE_RENDER_PT_caches_photongi_persistence(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = " "  # Label is drawn manually in draw_header() so we can make it inactive
    bl_parent_id = "LUXCORE_RENDER_PT_caches_photongi"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE" and context.scene.luxcore.config.engine == "PATH"

    def draw_header(self, context):
        self.layout.active = context.scene.luxcore.config.photongi.enabled
        self.layout.label(text="Persistence")

    def draw(self, context):
        draw_persistent_file_ui(context, self.layout, context.scene.luxcore.config.photongi)


class LUXCORE_RENDER_PT_caches_envlight(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Environment Light Cache"
    bl_parent_id = "LUXCORE_RENDER_PT_caches"
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

        layout.prop(envlight_cache, "quality")


class LUXCORE_RENDER_PT_caches_envlight_persistence(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = " "  # Label is drawn manually in draw_header() so we can make it inactive
    bl_parent_id = "LUXCORE_RENDER_PT_caches_envlight"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE" and context.scene.luxcore.config.engine == "PATH"

    def draw_header(self, context):
        self.layout.active = context.scene.luxcore.config.envlight_cache.enabled
        self.layout.label(text="Persistence")

    def draw(self, context):
        draw_persistent_file_ui(context, self.layout, context.scene.luxcore.config.envlight_cache)


class LUXCORE_RENDER_PT_caches_DLSC(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Direct Light Sampling Cache"
    bl_parent_id = "LUXCORE_RENDER_PT_caches"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw_header(self, context):
        self.layout.prop(context.scene.luxcore.config.dls_cache, "enabled", text="")

    def draw(self, context):
        config = context.scene.luxcore.config
        dls_cache = config.dls_cache
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.active = dls_cache.enabled
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
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        config = context.scene.luxcore.config
        dls_cache = config.dls_cache
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.active = context.scene.luxcore.config.dls_cache.enabled

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


class LUXCORE_RENDER_PT_caches_DLSC_persistence(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = " "  # Label is drawn manually in draw_header() so we can make it inactive
    bl_parent_id = "LUXCORE_RENDER_PT_caches_DLSC"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE" and context.scene.luxcore.config.engine == "PATH"

    def draw_header(self, context):
        self.layout.active = context.scene.luxcore.config.dls_cache.enabled
        self.layout.label(text="Persistence")

    def draw(self, context):
        draw_persistent_file_ui(context, self.layout, context.scene.luxcore.config.dls_cache)
