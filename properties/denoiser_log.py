import bpy
from bpy.types import PropertyGroup


class DenoiserLogEntry:
    def __init__(self, samples, elapsed_render_time, elapsed_denoiser_time, denoiser_settings):
        self.samples = samples
        self.elapsed_render_time = elapsed_render_time
        self.elapsed_denoiser_time = elapsed_denoiser_time

        self.scales = denoiser_settings.scales
        self.hist_dist_thresh = denoiser_settings.hist_dist_thresh
        self.patch_radius = denoiser_settings.patch_radius
        self.search_window_radius = denoiser_settings.search_window_radius
        self.filter_spikes = denoiser_settings.filter_spikes


class LuxCoreDenoiserLog(PropertyGroup):
    entries = []

    def add(self, entry):
        assert isinstance(entry, DenoiserLogEntry)
        self.entries.append(entry)

    def clear(self):
        self.entries.clear()
