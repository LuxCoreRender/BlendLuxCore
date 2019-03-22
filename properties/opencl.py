import bpy
from bpy.props import StringProperty, CollectionProperty, BoolProperty
from bpy.types import PropertyGroup
from ..bin import pyluxcore


class LuxCoreOpenCLDevice(PropertyGroup):
    enabled = BoolProperty(default=True)
    name = StringProperty()
    type = StringProperty()


class LuxCoreOpenCLSettings(PropertyGroup):
    # A collection of devices (can be enabled/disabled and have a name and type)
    devices = CollectionProperty(type=LuxCoreOpenCLDevice)
    # To check on .blend file loading if the devices are correct for this computer
    devices_hash = StringProperty()

    use_native_cpu = BoolProperty(name="Use CPUs", default=True,
                                  description="Use native C++ threads on the CPU (hybrid rendering)")

    def init_devices(self, device_list):
        print("Updating OpenCL device list")
        # Set hash here so it is also set when user forces init with operator
        new_devices_hash = self.get_devices_hash_str(device_list)
        self.devices_hash = new_devices_hash

        self.devices.clear()

        for device_tuple in device_list:
            self.devices.add()
            new = self.devices[-1]
            new.name = device_tuple[0]
            new.type = device_tuple[1]

    def update_devices_if_necessary(self):
        device_list = self.get_opencl_devices()
        new_devices_hash = self.get_devices_hash_str(device_list)

        if self.devices_hash != new_devices_hash:
            self.init_devices(device_list)
            return True
        return False

    def get_devices_hash_str(self, device_list):
        concat = ""
        for device_tuple in device_list:
            name = device_tuple[0]
            concat += name
        return concat

    def devices_to_selection_string(self):
        selection = ""

        for device in self.devices:
            enabled = device.enabled
            # Never use OpenCL CPU devices
            if device.type == "OPENCL_CPU":
                enabled = False
            selection += "1" if enabled else "0"

        return selection

    def get_opencl_devices(self):
        """
        Returns a list of tuples of the form:
        (name, type, compute_units, native_vector_width_float, max_memory, max_memory_alloc_size)
        where:
        - name is a name string, e.g. "Tahiti"
        - type is a string in ("ALL", "NATIVE_THREAD", "OPENCL_ALL", "OPENCL_DEFAULT",
          "OPENCL_CPU", "OPENCL_GPU", "OPENCL_UNKNOWN", "VIRTUAL", "UNKOWN")
          (most common is probably "OPENCL_CPU" and "OPENCL_GPU")
        """
        return pyluxcore.GetOpenCLDeviceList()
