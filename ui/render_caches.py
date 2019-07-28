import os
from bl_ui.properties_render import RenderButtonsPanel
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

###    def draw_header(self, context):
###        self.layout.prop(context.scene.luxcore.config.photongi, "enabled", text="")
##
    def draw(self, context):
#        photongi = context.scene.luxcore.config.photongi
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False      
##        
##        engine_is_bidir = context.scene.luxcore.config.engine == "BIDIR"
##        layout.enabled = photongi.enabled and not engine_is_bidir
##
##        if engine_is_bidir:
##            layout.label(text="Not supported by Bidir", icon=icons.INFO)
##
##        if not photongi.indirect_enabled and not photongi.caustic_enabled:
##            layout.label(text="All caches disabled", icon=icons.WARNING)
##
##        col = layout.column(align=True)
##        col.prop(photongi, "photon_maxcount")
##        col.prop(photongi, "photon_maxdepth")
##
##        col = layout.column(align=True)
##        col.prop(photongi, "indirect_enabled")
##
##        col = layout.column(align=True)
##        col.enabled = photongi.indirect_enabled
##
##        col = layout.column(align=True)
##        col.prop(photongi, "indirect_haltthreshold_preset")
##        if photongi.indirect_haltthreshold_preset == "custom":
##            col.prop(photongi, "indirect_haltthreshold_custom")
##        col.prop(photongi, "indirect_usagethresholdscale")
##        col.prop(photongi, "indirect_normalangle")
##        col.prop(photongi, "indirect_glossinessusagethreshold")
##        col = layout.column(align=True)
##        col.prop(photongi, "indirect_lookup_radius_auto")
##        if not photongi.indirect_lookup_radius_auto:
##            col.prop(photongi, "indirect_lookup_radius")
##
##        col = layout.column(align=True)
##        col.prop(photongi, "caustic_enabled")
##        col = layout.column(align=True)
##        col.enabled = photongi.caustic_enabled
##        sub = col.column(align=True)
##        sub.prop(photongi, "caustic_maxsize")
##        sub = col.column(align=True)
##        sub.prop(photongi, "caustic_lookup_radius")
##        sub.prop(photongi, "caustic_lookup_maxcount")
##        sub = col.column(align=True)
##        sub.prop(photongi, "caustic_normalangle")
##        sub = col.column(align=True)
##        sub.prop(photongi, "caustic_merge_enabled")
##        sub = col.column(align=True)
##        sub.enabled = photongi.caustic_merge_enabled
##        sub.prop(photongi, "caustic_merge_radius_scale")
##
##        col = layout.column(align=True)
##        col.prop(photongi, "debug")
##        if ((photongi.debug == "showindirect" or photongi.debug == "showindirectpathmix")
##                and not photongi.indirect_enabled) or (
##                photongi.debug == "showcaustic" and not photongi.caustic_enabled):
##            col.label(text="Can't show this cache (disabled)", icon=icons.WARNING)
##
##        file_abspath = utils.get_abspath(photongi.file_path, library=context.scene.library)
##        file_exists = os.path.isfile(file_abspath)
##
##        if not file_abspath:
##            cache_status = "Cache file will not be saved"
##        elif photongi.save_or_overwrite:
##            if file_exists:
##                cache_status = "Cache file exists, but will be overwritten"
##            else:
##                cache_status = "Cache file will be saved"
##        else:
##            if file_exists:
##                cache_status = "Will use cache from file"
##            else:
##                cache_status = "No cache file available"
##
##        col = layout.column(align=True)
##        col.prop(photongi, "save_or_overwrite",
##                 text="Compute and overwrite" if file_exists else "Compute and save")
##        col.prop(photongi, "file_path", text="")
##        col.label(text=cache_status)

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
