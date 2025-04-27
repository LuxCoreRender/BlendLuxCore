import bpy
from bpy.props import StringProperty, CollectionProperty, BoolProperty
from bpy.types import PropertyGroup
import pyluxcore
from ..utils import get_addon_preferences


class LuxCoreOpenCLDevice(PropertyGroup):
    enabled: BoolProperty(default=True)
    name: StringProperty()
    type: StringProperty()


class LuxCoreDeviceSettings(PropertyGroup):
    # A collection of devices (can be enabled/disabled and have a name and type)
    devices: CollectionProperty(type=LuxCoreOpenCLDevice)
    # To check on .blend file loading if the devices are correct for this computer
    devices_hash: StringProperty()

    use_native_cpu: BoolProperty(name="Use CPUs", default=True,
                                 description="Use native C++ threads on the CPU (hybrid rendering)")

    def init_devices(self, device_props):
        print("Updating device list")
        # Set hash here so it is also set when user forces init with operator
        new_devices_hash = self.get_devices_hash_str(device_props)
        self.devices_hash = new_devices_hash

        self.devices.clear()

        for prefix in device_props.GetAllUniqueSubNames("opencl.device"):
            new = self.devices.add()
            new.name = device_props.Get(prefix + ".name").GetString()
            new.type = device_props.Get(prefix + ".type").GetString()
            
            # Intel GPU devices can lead to crashes, so disable them by default
            if "intel" in new.name.lower():
                new.enabled = False

    def update_devices_if_necessary(self):
        device_props = self.get_device_props()
        new_devices_hash = self.get_devices_hash_str(device_props)

        if self.devices_hash != new_devices_hash:
            self.init_devices(device_props)
            return True
        return False

    def get_devices_hash_str(self, device_props):
        return str(device_props)

    def devices_to_selection_string(self):
        preferences = get_addon_preferences(bpy.context)
        selection = ""

        for device in self.devices:
            enabled = device.enabled
            # Never use OpenCL CPU devices
            if device.type == "OPENCL_CPU":
                enabled = False
            
            if device.type == "OPENCL_GPU" and preferences.gpu_backend != "OPENCL":
                enabled = False
            
            if device.type == "CUDA_GPU" and preferences.gpu_backend != "CUDA":
                enabled = False
            
            selection += "1" if enabled else "0"

        return selection

    def get_gpu_devices(self, context):
        gpu_backend = get_addon_preferences(context).gpu_backend
        if gpu_backend == "OPENCL":
            return [device for device in self.devices if device.type == "OPENCL_GPU"]
        elif gpu_backend == "CUDA":
            return [device for device in self.devices if device.type == "CUDA_GPU"]
        else:
            raise Exception("Unknown GPU Backend")

    def get_device_props(self):
        """
        Returns pyluxcore.Properties() of the following form:
        
        opencl.device.0.platform.name = "NVIDIA Corporation
        opencl.device.0.platform.version = "OpenCL 1.2 CUDA 10.2.141
        opencl.device.0.name = "GeForce RTX 2080"
        opencl.device.0.type = "OPENCL_GPU"
        opencl.device.0.units = 46
        opencl.device.0.clock = 1815
        opencl.device.0.nativevectorwidthfloat = 1
        opencl.device.0.maxmemory = 8366784512
        opencl.device.0.maxmemoryallocsize = 2091696128
        opencl.device.0.localmemory = 49152
        opencl.device.0.constmemory = 65536
        opencl.device.1.platform.name = "Intel(R) Corporation
        opencl.device.1.platform.version = "OpenCL 2.1 LINUX
        opencl.device.1.name = "AMD Ryzen 7 2700X Eight-Core Processor         "
        opencl.device.1.type = "OPENCL_CPU"
        opencl.device.1.units = 16
        opencl.device.1.clock = 0
        opencl.device.1.nativevectorwidthfloat = 8
        opencl.device.1.maxmemory = 33686577152
        opencl.device.1.maxmemoryallocsize = 8421644288
        opencl.device.1.localmemory = 32768
        opencl.device.1.constmemory = 131072
        """
        return pyluxcore.GetOpenCLDeviceDescs()
