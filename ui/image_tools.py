from bpy.types import Panel
from . import denoiser
from ..utils.refresh_button import template_refresh_button
from ..utils import ui as utils_ui
from ..engine import LuxCoreRenderEngine
from . import icons


class LuxCoreImagePanel:
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "LuxCore"

    @classmethod
    def poll(cls, context):
        image = context.space_data.image
        return context.scene.render.engine == "LUXCORE" and image and image.type == "RENDER_RESULT"


class LUXCORE_IMAGE_PT_display(Panel, LuxCoreImagePanel):
    bl_label = "Display"

    def draw(self, context):
        layout = self.layout
        display = context.scene.luxcore.display
        config = context.scene.luxcore.config

        text = "Resume" if display.paused else "Pause"
        icon = "PLAY" if display.paused else "PAUSE"
        row = layout.row()
        row.enabled = LuxCoreRenderEngine.final_running
        row.prop(display, "paused", text=text, icon=icon, toggle=True)

        template_refresh_button(display, "refresh", layout, "Refreshing film...")
        layout.prop(display, "interval")

        if config.engine == "PATH" and config.use_tiles:
            col = layout.column(align=True)
            col.prop(display, "show_converged")
            col.prop(display, "show_notconverged")
            col.prop(display, "show_pending")
            layout.prop(display, "show_passcounts")


class LUXCORE_IMAGE_PT_denoiser(Panel, LuxCoreImagePanel):
    bl_label = "Denoiser"

    def draw(self, context):
        layout = self.layout
        image = context.space_data.image

        denoiser.draw(context, layout)

        col = layout.column()
        col.label("Change the pass to see the result", icon=icons.INFO)
        if image:
            iuser = context.space_data.image_user
            col.template_image_layers(image, iuser)

        log_entries = context.scene.luxcore.denoiser_log.entries
        if log_entries:
            entry = log_entries[-1]
            col = layout.column(align=True)
            box = col.box()
            box.label("Denoised Image Stats", icon="IMAGE_DATA")
            box = col.box()
            subcol = box.column()
            subcol.label("Samples: %d" % entry.samples)
            subcol.label("Render Time: " + utils_ui.humanize_time(entry.elapsed_render_time))
            subcol.label("Denoising Duration: " + utils_ui.humanize_time(entry.elapsed_denoiser_time))

            if context.scene.luxcore.denoiser.type == "BCD":
                box = col.box()
                subcol = box.column()
                subcol.label("Last Denoiser Settings:", icon="UI")
                subcol.label("Remove Fireflies: " + ("Enabled" if entry.filter_spikes else "Disabled"))
                subcol.label("Histogram Distance Threshold: " + str(entry.hist_dist_thresh))
                subcol.label("Search Window Radius: " + str(entry.search_window_radius))
                subcol.label("Scales: " + str(entry.scales))
                subcol.label("Patch Radius: " + str(entry.patch_radius))


class LUXCORE_IMAGE_PT_statistics(Panel, LuxCoreImagePanel):
    bl_label = "Statistics"

    def draw(self, context):
        layout = self.layout
        image = context.space_data.image
        statistics_collection = context.scene.luxcore.statistics
        active_index = image.render_slots.active_index

        if len(context.scene.render.layers) > 1:
            layout.label("Only stats of last rendered render layer are shown", icon=icons.WARNING)

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
        if not stat.can_compare():
            return "NONE"

        if stat.is_better(other_stat):
            return "COLOR_GREEN"
        elif stat.is_equal(other_stat):
            return "COLOR_BLUE"
        else:
            return "COLOR_RED"

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
                col.label(stat.name)

            col = split.column()
            for stat in stat_list:
                col.label(str(stat))

    def draw_stat_comparison(self, context, stats, other_stats, layout):
        statistics_collection = context.scene.luxcore.statistics

        stat_lists = self.stat_lists_by_category(stats)
        other_stat_lists = self.stat_lists_by_category(other_stats)

        # Header
        split = layout.split()
        split.label()
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
                col.label(stat.name)

            # The column for the first stats
            col = split.column()
            # col.prop(statistics_collection, "first_slot", text="")
            for stat, other_stat in comparison_stat_list:
                col.label(str(stat), icon=self.icon(stat, other_stat))

            # The column for the other stats
            col = split.column()
            # col.prop(statistics_collection, "second_slot", text="")
            for stat, other_stat in comparison_stat_list:
                col.label(str(other_stat), icon=self.icon(other_stat, stat))
