import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty
from ..utils.statistics import (
    Stat,
    bool_to_string,
    clamping_to_string,
    get_rays_per_sample,
    get_rounded,
    get_vram_usage,
    greater_is_better,
    path_depths_to_string,
    rays_per_sample_to_string,
    samples_per_sec_to_string,
    smaller_is_better,
    time_to_string,
    triangle_count_to_string,
    vram_better,
    vram_usage_to_string,
)


class LuxCoreRenderStats:
    def __init__(self):
        # Some stats use rounding getter functions, because it is better for the user
        # if values that only differ by a very small amount appear as equal in the UI.

        categories = []
        categories.append("Statistics")
        self.render_time = Stat("Render Time", categories[-1],
                                0, smaller_is_better, time_to_string, get_rounded)
        self.samples_eye = Stat("Samples", categories[-1], 0, greater_is_better)
        categories.append("Performance")
        self.samples_per_sec = Stat("Samples/Sec", categories[-1],
                                    0, greater_is_better, samples_per_sec_to_string, get_rounded)
        self.rays_per_sample = Stat("Rays/Sample", categories[-1],
                                    0, smaller_is_better, rays_per_sample_to_string, get_rounded)
        categories.append("Startup")
        self.export_time = Stat("Export Time", categories[-1],
                                0, smaller_is_better, time_to_string, get_rounded)
        self.export_time_meshes = Stat("    Mesh Export Time", categories[-1],
                                       0, smaller_is_better, time_to_string, get_rounded)
        self.export_time_hair = Stat("    Hair Export Time", categories[-1],
                                     0, smaller_is_better, time_to_string, get_rounded)
        self.export_time_instancing = Stat("    Instancing Time", categories[-1],
                                           0, smaller_is_better, time_to_string, get_rounded)
        self.session_init_time = Stat("Session Init Time", categories[-1],
                                      0, smaller_is_better, time_to_string, get_rounded)
        categories.append("Scene")
        self.light_count = Stat("Lights", categories[-1], 0)
        self.triangle_count = Stat("Triangles", categories[-1], 0, string_func=triangle_count_to_string)
        self.vram = Stat("VRAM", categories[-1], (0, 0), vram_better, vram_usage_to_string)
        categories.append("Settings")
        self.render_engine = Stat("Engine", categories[-1], "?")
        self.use_hybridbackforward = Stat("Add Light Tracing", categories[-1], False, string_func=bool_to_string)
        self.samples_light_tracing = Stat("Light T. Samples", categories[-1], 0, greater_is_better)
        self.sampler = Stat("Sampler", categories[-1], "?")
        self.clamping = Stat("Clamping", categories[-1], 0, string_func=clamping_to_string)
        self.path_depths = Stat("Path Depths", categories[-1], tuple(), string_func=path_depths_to_string)
        categories.append("Caches")
        self.cache_indirect = Stat("Indirect Light Cache", categories[-1], False, string_func=bool_to_string)
        self.cache_caustics = Stat("Caustics Cache", categories[-1], False, string_func=bool_to_string)
        self.cache_envlight = Stat("Env. Light Cache", categories[-1], False, string_func=bool_to_string)
        self.cache_dls = Stat("DLS Cache", categories[-1], False, string_func=bool_to_string)

        self.members = [getattr(self, attr) for attr in dir(self)
                        if not callable(getattr(self, attr)) and not attr.startswith("__")]
        self.members.sort(key=lambda stat: stat.id)

        self.categories = categories

    def to_list(self):
        return self.members

    def reset(self):
        for stat in self.to_list():
            stat.reset()

    def update_from_luxcore_stats(self, stat_props):
        self.render_time.value = stat_props.Get("stats.renderengine.time").GetFloat()
        self.samples_eye.value = stat_props.Get("stats.renderengine.pass.eye").GetInt()
        self.samples_light_tracing.value = stat_props.Get("stats.renderengine.pass.light").GetInt()
        self.samples_per_sec.value = stat_props.Get("stats.renderengine.total.samplesec").GetFloat()
        self.triangle_count.value = stat_props.Get("stats.dataset.trianglecount").GetUnsignedLongLong()
        self.rays_per_sample.value = get_rays_per_sample(stat_props)
        self.vram.value = get_vram_usage(stat_props)


class LuxCoreRenderStatsCollection(PropertyGroup):
    # Important: All access to _slots needs to be through the __getitem__ method so we can add slots if necessary!
    _slots = [LuxCoreRenderStats() for i in range(8)]

    compare: BoolProperty(name="Compare", default=False,
                           description="Compare the statistics of two slots")

    def generate_slot_items(self, index_offset=0):
        render_result = self._get_render_result()
        if not render_result:
            return

        slot_names = [(slot.name or "Slot %d" % (i + 1))
                      for i, slot in enumerate(render_result.render_slots)]
        items = [(str(i), name, "", i + index_offset) for i, name in enumerate(slot_names)]
        return items

    def first_slot_items_callback(self, context):
        # The special "current" entry should be the default, so we give it index 0
        items = self.generate_slot_items(index_offset=1)
        items.insert(0, ("current", "Current", "Use the currently selected slot", 0))
        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        LuxCoreRenderStatsCollection.first_slot_callback_strings = items
        return items

    def second_slot_items_callback(self, context):
        items = self.generate_slot_items()
        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        LuxCoreRenderStatsCollection.second_slot_callback_strings = items
        return items

    first_slot: EnumProperty(name="First Slot", description="The first slot",
                              items=first_slot_items_callback)
    second_slot: EnumProperty(name="Second Slot", description="The other slot to compare with",
                               items=second_slot_items_callback)

    def __getitem__(self, slot_index):
        """
        Important: All access to self._slots needs to be through this method so we can add slots if necessary!
        """
        while len(self._slots) < slot_index + 1:
            self._slots.append(LuxCoreRenderStats())
        return self._slots[slot_index]

    def reset(self, slot_index):
        self[slot_index].reset()

    def get_active(self):
        """
        Returns the slot currently selected for viewing by the user.
        Note that this is not necessarily the slot currently being
        rendered (only at the very beginning of the rendering).
        """
        render_result = self._get_render_result()
        if not render_result:
            return self[0]

        slot_index = render_result.render_slots.active_index
        return self[slot_index]

    def _get_render_result(self):
        for image in bpy.data.images:
            if image.type == "RENDER_RESULT":
                return image
        return None
