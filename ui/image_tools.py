from bpy.types import Panel
from ..utils.refresh_button import template_refresh_button
from ..utils import ui as utils_ui
from ..engine.base import LuxCoreRenderEngine
from . import icons
from ..properties.denoiser import LuxCoreDenoiser
from ..properties.display import LuxCoreDisplaySettings


class LuxCoreImagePanel:
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "LuxCore"

    @classmethod
    def poll(cls, context):
        image = context.space_data.image
        return context.scene.render.engine == "LUXCORE" and image and image.type == "RENDER_RESULT"


class LUXCORE_IMAGE_PT_display(Panel, LuxCoreImagePanel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "LuxCore"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        display = scene.luxcore.display
        config = scene.luxcore.config

        text = "Resume" if LuxCoreDisplaySettings.paused else "Pause"
        icon = "PLAY" if LuxCoreDisplaySettings.paused else "PAUSE"
        row = layout.row()
        row.enabled = LuxCoreRenderEngine.final_running
        row.operator("luxcore.toggle_pause", text=text, icon=icon)

        template_refresh_button(LuxCoreDisplaySettings.refresh, "luxcore.request_display_refresh",
                                layout, "Refreshing film...")
        layout.prop(display, "interval")

        if config.engine == "PATH" and config.use_tiles:
            col = layout.column(align=True)
            col.prop(display, "show_converged")
            col.prop(display, "show_notconverged")
            col.prop(display, "show_pending")
            layout.prop(display, "show_passcounts")


class LUXCORE_IMAGE_PT_denoiser(Panel, LuxCoreImagePanel):
    bl_label = "Denoiser"
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        image = context.space_data.image

        config = context.scene.luxcore.config
        denoiser = context.scene.luxcore.denoiser

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(denoiser, "type", expand=False)
        col.enabled = denoiser.enabled and not LuxCoreRenderEngine.final_running

        if denoiser.enabled and denoiser.type == "BCD":
            if config.sampler == "METROPOLIS" and not config.use_tiles:
                layout.label(text="Metropolis sampler can lead to artifacts!", icon=icons.WARNING)

        sub = layout.column(align=True)
        # The user should not be able to request a refresh when denoiser is disabled
        sub.enabled = denoiser.enabled
        template_refresh_button(LuxCoreDenoiser.refresh, "luxcore.request_denoiser_refresh",
                                sub, "Running denoiser...")

        col = layout.column()
        col.label(text="Change the pass to see the result", icon=icons.INFO)
        if image:
            iuser = context.space_data.image_user
            col.template_image_layers(image, iuser)

        log_entries = context.scene.luxcore.denoiser_log.entries
        if log_entries:
            entry = log_entries[-1]
            col = layout.column(align=True)
            box = col.box()
            box.label(text="Denoised Image Stats", icon="IMAGE_DATA")
            box = col.box()
            subcol = box.column()
            subcol.label(text="Samples: %d" % entry.samples)
            subcol.label(text="Render Time: " + utils_ui.humanize_time(entry.elapsed_render_time))
            subcol.label(text="Denoising Duration: " + utils_ui.humanize_time(entry.elapsed_denoiser_time))

            if context.scene.luxcore.denoiser.type == "BCD":
                box = col.box()
                subcol = box.column()
                subcol.label(text="Last Denoiser Settings:", icon="UI")
                subcol.label(text="Remove Fireflies: " + ("Enabled" if entry.filter_spikes else "Disabled"))
                subcol.label(text="Histogram Distance Threshold: " + str(entry.hist_dist_thresh))
                subcol.label(text="Search Window Radius: " + str(entry.search_window_radius))
                subcol.label(text="Scales: " + str(entry.scales))
                subcol.label(text="Patch Radius: " + str(entry.patch_radius))


class LUXCORE_IMAGE_PT_statistics(Panel, LuxCoreImagePanel):
    bl_label = "Statistics"
    bl_order = 3

    def draw(self, context):
        layout = self.layout
        image = context.space_data.image
        statistics_collection = context.scene.luxcore.statistics
        active_index = image.render_slots.active_index

        if len(context.scene.view_layers) > 1:
           layout.label(text="Only stats of last rendered render layer are shown", icon=icons.WARNING)

        layout.prop(statistics_collection, "compare")

        if statistics_collection.compare:
            if statistics_collection.first_slot == "current":
                first_index = active_index
            else:
                first_index = int(statistics_collection.first_slot)
            stats = statistics_collection[first_index]

            other_index = int(statistics_collection.second_slot)
            other_stats = statistics_collection[other_index]
            self.draw_stat_comparison(context, stats, other_stats, layout)
        else:
            stats = statistics_collection[active_index]
            self.draw_stats(stats, layout)

    @staticmethod
    def icon(stat, other_stat):
        return "NONE"
        # TODO 2.8 try to find good icons for better/worse/equal
        # if not stat.can_compare():
        #     return "NONE"
        #
        # if stat.is_better(other_stat):
        #     return "COLOR_GREEN"
        # elif stat.is_equal(other_stat):
        #     return "COLOR_BLUE"
        # else:
        #     return "COLOR_RED"

    def stat_lists_by_category(self, stats):
        stat_lists = []
        for category in stats.categories:
            stat_lists.append([s for s in stats.to_list() if s.category == category])
        return stat_lists

    def draw_stats(self, stats, layout):
        stat_lists = self.stat_lists_by_category(stats)

        parentcol = layout.column(align=True)
        for stat_list in stat_lists:
            box = parentcol.box()
            split = box.split()

            col = split.column()
            for stat in stat_list:
                col.label(text=stat.name)

            col = split.column()
            for stat in stat_list:
                col.label(text=str(stat))

    def draw_stat_comparison(self, context, stats, other_stats, layout):
        statistics_collection = context.scene.luxcore.statistics

        stat_lists = self.stat_lists_by_category(stats)
        other_stat_lists = self.stat_lists_by_category(other_stats)

        # Header
        split = layout.split()
        split.label(text="")
        split.prop(statistics_collection, "first_slot", text="")
        split.prop(statistics_collection, "second_slot", text="")

        parentcol = layout.column(align=True)
        for stat_list, other_stat_list in zip(stat_lists, other_stat_lists):
            comparison_stat_list = tuple(zip(stat_list, other_stat_list))

            box = parentcol.box()
            split = box.split()

            # The column for the labels
            col = split.column()
            for stat, _ in comparison_stat_list:
                col.label(text=stat.name)

            # The column for the first stats
            col = split.column()
            # col.prop(statistics_collection, "first_slot", text="")
            for stat, other_stat in comparison_stat_list:
                col.label(text=str(stat), icon=self.icon(stat, other_stat))

            # The column for the other stats
            col = split.column()
            # col.prop(statistics_collection, "second_slot", text="")
            for stat, other_stat in comparison_stat_list:
                col.label(text=str(other_stat), icon=self.icon(other_stat, stat))
