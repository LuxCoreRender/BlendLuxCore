import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty
from ..utils import ui as utils_ui


def smaller_is_better(first, second):
    return first < second


def greater_is_better(first, second):
    return first > second


def time_to_string(seconds):
    return utils_ui.humanize_time(seconds,
                                  show_subseconds=True,
                                  subsecond_places=1)


def samples_per_sec_to_string(samples_per_sec):
    if samples_per_sec >= 10 ** 6:
        # Use megasamples as unit
        return "%.1f M" % (samples_per_sec / 10 ** 6)
    else:
        # Use kilosamples as unit
        return "%d k" % (samples_per_sec / 10 ** 3)


def triangle_count_to_string(triangle_count):
    if triangle_count >= 10 ** 6:
        return "%.1f M" % (triangle_count / 10 ** 6)
    else:
        return "{:,}".format(triangle_count)


class Stat:
    def __init__(self, name, init_value, better_func=None, string_func=str):
        self.name = name
        self.init_value = init_value
        self.value = init_value
        self.better_func = better_func
        self.string_func = string_func

    def reset(self):
        self.value = self.init_value

    def can_compare(self):
        return self.better_func is not None

    def is_better(self, other):
        return self.better_func(self.value, other.value)

    def is_equal(self, other):
        return self.value == other.value

    def __str__(self):
        return self.string_func(self.value)


class LuxCoreRenderStats:
    def __init__(self):
        self.export_time = Stat("Export Time", 0, smaller_is_better, time_to_string)
        self.session_init_time = Stat("Session Init Time", 0, smaller_is_better, time_to_string)
        self.render_time = Stat("Render Time", 0, greater_is_better, time_to_string)
        self.samples = Stat("Samples", 0, greater_is_better)
        self.samples_per_sec = Stat("Samples/Sec", 0, greater_is_better, samples_per_sec_to_string)
        self.light_count = Stat("Lights", 0)
        self.object_count = Stat("Objects", 0)
        self.triangle_count = Stat("Triangles", 0, string_func=triangle_count_to_string)
        self.render_engine = Stat("Engine", "")
        self.sampler = Stat("Sampler", "")

        # TODO more:
        # Rays/Sample
        # a custom string?
        # etc.

    def to_list(self):
        # TODO how to get stable sorted list?
        members = [getattr(self, attr) for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        return members

    def reset(self):
        for stat in self.to_list():
            stat.reset()

    def update_from_luxcore_stats(self, stats):
        self.render_time.value = stats.Get("stats.renderengine.time").GetFloat()
        self.samples.value = stats.Get("stats.renderengine.pass").GetInt()
        # TODO convergence
        self.samples_per_sec.value = stats.Get("stats.renderengine.total.samplesec").GetFloat()
        self.triangle_count.value = stats.Get("stats.dataset.trianglecount").GetUnsignedLongLong()


class LuxCoreRenderStatsCollection(PropertyGroup):
    slots = [LuxCoreRenderStats() for i in range(8)]

    compare = BoolProperty(name="Compare", default=False,
                           description="Compare the statistics of two slots")

    def slot_items_callback(self, context):
        render_result = self._get_render_result()
        if not render_result:
            return

        slot_names = [(slot.name if slot.name else "Slot %d" % (i + 1))
                      for i, slot in enumerate(render_result.render_slots)]
        items = [(str(i), name, "", i) for i, name in enumerate(slot_names)]
        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        LuxCoreRenderStatsCollection.callback_strings = items
        return items

    comparison_slot = EnumProperty(name="Slot", description="The other slot to compare with",
                                   items=slot_items_callback)

    def __getitem__(self, slot_index):
        return self.slots[slot_index]

    def reset(self, slot_index):
        self.slots[slot_index].reset()

    def get_active(self):
        render_result = self._get_render_result()
        if not render_result:
            return None

        slot_index = render_result.render_slots.active_index
        return self.slots[slot_index]

    def _get_render_result(self):
        for image in bpy.data.images:
            if image.type == "RENDER_RESULT":
                return image
        return None
