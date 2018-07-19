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


def get_rounded(value):
    return round(value, 1)


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


def path_depths_to_string(depths):
    if not depths:
        return ""

    if len(depths) == 2:
        # Bidir (eye/light)
        return "Eye %d, Light %d" % depths
    elif len(depths) == 4:
        # Path (total/diffuse/glossy/specular)
        return "T %d (D %d, G %d, S %d)" % depths
    else:
        raise NotImplementedError("Unkown number of depth values")


def clamping_to_string(clamping):
    if clamping == 0:
        return "Disabled"
    elif clamping < 1:
        return str(round(clamping, 5))
    else:
        return str(round(clamping, 1))


class Stat:
    id = 0

    def __init__(self, name, init_value, better_func=None, string_func=str, get_value_func=None):
        self.name = name
        self.init_value = init_value
        self._value = init_value
        self.better_func = better_func
        self.string_func = string_func
        self.get_value_func = get_value_func

        # ID for sorting of the stats in the UI
        self.id = Stat.id
        Stat.id += 1

    @property
    def value(self):
        if self.get_value_func:
            return self.get_value_func(self._value)
        else:
            return self._value

    @value.setter
    def value(self, value):
        self._value = value

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
        # Some stats use rounding getter functions, because it is better for the user
        # if values that only differ by a very small amount appear as equal in the UI.
        self.export_time = Stat("Export Time", 0, smaller_is_better, time_to_string, get_rounded)
        self.session_init_time = Stat("Session Init Time", 0, smaller_is_better, time_to_string, get_rounded)
        self.render_time = Stat("Render Time", 0, greater_is_better, time_to_string, get_rounded)
        self.samples = Stat("Samples", 0, greater_is_better)
        self.samples_per_sec = Stat("Samples/Sec", 0, greater_is_better, samples_per_sec_to_string)
        self.light_count = Stat("Lights", 0)
        self.object_count = Stat("Objects", 0)
        self.triangle_count = Stat("Triangles", 0, string_func=triangle_count_to_string)
        self.render_engine = Stat("Engine", "")
        self.sampler = Stat("Sampler", "")
        self.light_strategy = Stat("Light Strategy", "")
        self.path_depths = Stat("Path Depths", tuple(), string_func=path_depths_to_string)
        self.clamping = Stat("Clamping", 0, string_func=clamping_to_string)

        # TODO more:
        # custom props (e.g. from config)?
        # Rays/Sample
        # VRAM usage (OpenCL only)
        # a custom string?
        # put denoiser settings/stats also here?
        # etc.

        # TODO some sort of categories, e.g. settings and statistics

    def to_list(self):
        members = [getattr(self, attr) for attr in dir(self)
                   if not callable(getattr(self, attr)) and not attr.startswith("__")]
        members.sort(key=lambda stat: stat.id)
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

    first_slot = EnumProperty(name="Slot", description="The first slot",
                              items=first_slot_items_callback)
    second_slot = EnumProperty(name="Slot", description="The other slot to compare with",
                               items=second_slot_items_callback)

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
