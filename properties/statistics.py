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


def convergence_to_string(convergence):
    if convergence < 0.95:
        return "%d%%" % round(convergence * 100)
    else:
        return "%.2f%%" % (convergence * 100)


def rays_per_sample_to_string(rays_per_sample):
    return "%.1f" % rays_per_sample


def get_rays_per_sample(stat_props):
    samples_per_sec = stat_props.Get("stats.renderengine.total.samplesec").GetFloat()
    rays = stat_props.Get("stats.renderengine.performance.total").GetFloat()
    if samples_per_sec > 0:
        return rays / samples_per_sec
    else:
        return 0


def get_vram_usage(stat_props):
    device_names = stat_props.Get("stats.renderengine.devices")

    max_memory = float('inf')
    used_memory = 0

    for i in range(device_names.GetSize()):
        device_name = device_names.GetString(i)
        if device_name.startswith("NativeIntersect"):
            # CPU cores do not report their memory usage, ignore them
            continue

        # Max memory available is limited by the device with least amount of memory
        device_max_memory = stat_props.Get("stats.renderengine.devices." + device_name + ".memory.total").GetFloat()
        device_max_memory = int(device_max_memory / (1024 * 1024))
        if device_max_memory < max_memory:
            max_memory = device_max_memory

        device_used_memory = stat_props.Get("stats.renderengine.devices." + device_name + ".memory.used").GetFloat()
        device_used_memory = int(device_used_memory / (1024 * 1024))
        if device_used_memory > used_memory:
            used_memory = device_used_memory

    if max_memory == float('inf'):
        max_memory = 0

    return used_memory, max_memory


def vram_usage_to_string(usage_tuple):
    used_memory, max_memory = usage_tuple
    return "%d MiB/%d MiB" % (used_memory, max_memory)


def vram_better(first_usage_tuple, second_usage_tuple):
    first_used_memory, _ = first_usage_tuple
    second_used_memory, _ = second_usage_tuple
    return first_used_memory < second_used_memory
    
    
def bool_to_string(value):
    if value:
        return "Enabled"
    else:
        return "Disabled"


class Stat:
    id = 0

    def __init__(self, name, category, init_value, better_func=None, string_func=str, get_value_func=None):
        self.name = name
        self.category = category
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
