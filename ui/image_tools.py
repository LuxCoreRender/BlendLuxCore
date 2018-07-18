from bpy.types import Panel
from . import denoiser
from ..utils.refresh_button import template_refresh_button
from ..utils import ui as utils_ui
from ..engine import LuxCoreRenderEngine


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
        col.label("Change the pass to see the result", icon="INFO")
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

    # TODO idea: comparison mode, select another slot index,
    # values will be side by side and the better ones are green/worse are red

    # TODO idea: comparison with the stats of the last run in this slot (keep them around for this purpose)

    # split = layout.split()
    # name = split.column()
    # name.label()
    # name.label("Export Time:")
    # name.label("Render Time:")
    # name.label("Samples:")
    # name.label("MSamples/Sec:")
    #
    # a = split.column()
    # a.label("slot 1")
    # a.label("10 seconds", icon="COLOR_GREEN")
    # a.label("10 seconds", icon="COLOR_RED")
    # a.label("50", icon="COLOR_RED")
    # a.label("3.4", icon="COLOR_BLUE")
    #
    #
    # b = split.column()
    # b.label("slot 4")
    # b.label("34.5 seconds", icon="COLOR_RED")
    # b.label("40 seconds", icon="COLOR_GREEN")
    # b.label("400", icon="COLOR_GREEN")
    # b.label("3.4", icon="COLOR_BLUE")

    def draw(self, context):
        layout = self.layout
        image = context.space_data.image
        slot_index = image.render_slots.active_index
        stats = context.scene.luxcore.statistics[slot_index]

        test_stats = context.scene.luxcore.statistics[4]

        # layout.label("Export Time: " + utils_ui.humanize_time(stats.export_time,
        #                                                       show_subseconds=True,
        #                                                       subsecond_places=1))

        self.draw_stats(stats, layout)
        layout.separator()
        self.draw_stat_comparison(stats, test_stats, layout)

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

    def draw_stats(self, stats, layout):
        stat_list = stats.to_list()

        split = layout.split()

        col = split.column()
        for stat in stat_list:
            col.label(stat.name)

        col = split.column()
        for stat in stat_list:
            col.label(str(stat))

    def draw_stat_comparison(self, stats, other_stats, layout):
        comparison_stat_list = tuple(zip(stats.to_list(), other_stats.to_list()))

        split = layout.split()

        col = split.column()
        for stat, _ in comparison_stat_list:
            col.label(stat.name)

        col = split.column()
        for stat, other_stat in comparison_stat_list:
            col.label(str(stat), icon=self.icon(stat, other_stat))

        col = split.column()
        for stat, other_stat in comparison_stat_list:
            col.label(str(other_stat), icon=self.icon(other_stat, stat))
