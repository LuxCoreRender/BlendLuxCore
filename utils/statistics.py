from . import ui as utils_ui

class TileStats:

    width = 0
    height = 0
    film_width = 0
    film_height = 0
    pending_coords = []
    pending_passcounts = []
    converged_coords = []
    converged_passcounts = []
    notconverged_coords = []
    notconverged_passcounts = []

    @classmethod
    def reset(cls):
        cls.width = 0
        cls.height = 0
        cls.film_width = 0
        cls.film_height = 0
        cls.pending_coords = []
        cls.pending_passcounts = []
        cls.converged_coords = []
        cls.converged_passcounts = []
        cls.notconverged_coords = []
        cls.notconverged_passcounts = []


def smaller_is_better(first, second):
    return first < second


def greater_is_better(first, second):
    return first > second


def time_to_string(seconds):
    return utils_ui.humanize_time(
        seconds, show_subseconds=True, subsecond_places=1
    )


def get_rounded(value):
    return round(value, 1)


def samples_per_sec_to_string(samples_per_sec):
    if samples_per_sec >= 10**6:
        # Use megasamples as unit
        return "%.1f M" % (samples_per_sec / 10**6)
    else:
        # Use kilosamples as unit
        return "%d k" % (samples_per_sec / 10**3)


def triangle_count_to_string(triangle_count):
    if triangle_count >= 10**6:
        return "%.1f M" % (triangle_count / 10**6)
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
    samples_per_sec = stat_props.Get(
        "stats.renderengine.total.samplesec"
    ).GetFloat()
    rays = stat_props.Get("stats.renderengine.performance.total").GetFloat()
    if samples_per_sec > 0:
        return rays / samples_per_sec
    else:
        return 0


def get_vram_usage(stat_props):
    device_names = stat_props.Get("stats.renderengine.devices")

    max_memory = float("inf")
    used_memory = 0

    for i in range(device_names.GetSize()):
        device_name = device_names.GetString(i)
        if device_name.startswith("NativeIntersect"):
            # CPU cores do not report their memory usage, ignore them
            continue

        # Max memory available is limited by the device with least amount of memory
        device_max_memory = stat_props.Get(
            "stats.renderengine.devices." + device_name + ".memory.total"
        ).GetFloat()
        device_max_memory = int(device_max_memory / (1024 * 1024))
        if device_max_memory < max_memory:
            max_memory = device_max_memory

        device_used_memory = stat_props.Get(
            "stats.renderengine.devices." + device_name + ".memory.used"
        ).GetFloat()
        device_used_memory = int(device_used_memory / (1024 * 1024))
        if device_used_memory > used_memory:
            used_memory = device_used_memory

    if max_memory == float("inf"):
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

    def __init__(
        self,
        name,
        category,
        init_value,
        better_func=None,
        string_func=str,
        get_value_func=None,
    ):
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
