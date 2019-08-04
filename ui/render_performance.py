from bl_ui.properties_render import RenderButtonsPanel
from bpy.types import Panel
from . import bpy
from .. import utils
from . import icons


class LUXCORE_RENDER_PT_performance(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "Performance"
    bl_order = 5

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def _draw_devices(self, layout, devices):
        layout.use_property_split = True
        layout.use_property_decorate = False      
        for device in devices:
            layout.prop(device, "enabled", text=device.name)

    def _show_hybrid_metropolis_warning(self, context):
        config = context.scene.luxcore.config
        opencl = context.scene.luxcore.opencl
        return (config.engine == "PATH" and config.device == "OCL"
                and config.sampler == "METROPOLIS" and opencl.use_native_cpu)

    def _show_openCL_device_warning(self, context):
        config = context.scene.luxcore.config
        opencl = context.scene.luxcore.opencl
        
        gpu_devices = [device for device in opencl.devices if device.type == "OPENCL_GPU"]
        # We don't show OpenCL CPU devices, we just need them to check if there are other devices
        cpu_devices = [device for device in opencl.devices if device.type == "OPENCL_CPU"]
        other_devices = set(opencl.devices) - (set(gpu_devices) | set(cpu_devices))

        has_gpus = any([device.enabled for device in gpu_devices])
        has_others = any([device.enabled for device in other_devices])

        return (config.engine == "PATH" and config.device == "OCL" and not has_gpus and not has_others)

    def draw_header(self, context):
        opencl = context.scene.luxcore.opencl
        layout = self.layout
        
        if self._show_hybrid_metropolis_warning(context):
            self.layout.label(text="", icon=icons.WARNING)

        if self._show_openCL_device_warning(context):
            layout.label(text="", icon=icons.WARNING)

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        opencl = context.scene.luxcore.opencl

        layout.use_property_split = True
        layout.use_property_decorate = False      

        if config.engine == "PATH" and config.device == "OCL":
            if not utils.is_opencl_build():
                # pyluxcore was compiled without OpenCL support
                layout.label(text="No OpenCL support in this BlendLuxCore version", icon=icons.ERROR)
        else:
            # CPU settings for native C++ threads            
            layout.prop(context.scene.render, "threads_mode", text = "CPU threads", expand=False)
            sub = layout.column(align=True)
            sub.enabled = context.scene.render.threads_mode == 'FIXED'
            sub.prop(context.scene.render, "threads")


class LUXCORE_RENDER_PT_performance_cpu_devices(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "CPU Devices"
    bl_parent_id = "LUXCORE_RENDER_PT_performance"
    lux_predecessor = "LUXCORE_RENDER_PT_performance_gpu_devices"

    @classmethod
    def poll(cls, context):
        config = context.scene.luxcore.config        
        return context.scene.render.engine == "LUXCORE" and config.engine == "PATH" and config.device == "OCL"

    def _show_hybrid_metropolis_warning(self, context):
        config = context.scene.luxcore.config
        opencl = context.scene.luxcore.opencl
        return (config.engine == "PATH" and config.device == "OCL"
                and config.sampler == "METROPOLIS" and opencl.use_native_cpu)

    def draw_header(self, context):
        opencl = context.scene.luxcore.opencl
        layout = self.layout
        layout.prop(opencl, "use_native_cpu", text="")

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config
        opencl = context.scene.luxcore.opencl

        layout.enabled = opencl.use_native_cpu

        layout.use_property_split = True
        layout.use_property_decorate = False
        
        # CPU settings for native C++ threads            
        layout.prop(context.scene.render, "threads_mode", text = "CPU threads", expand=False)
        sub = layout.column(align=True)
        sub.enabled = context.scene.render.threads_mode == 'FIXED'
        sub.prop(context.scene.render, "threads")

        if self._show_hybrid_metropolis_warning(context):
            col = layout.column(align=True)
            col.label(text="CPU should be disabled if Metropolis", icon=icons.WARNING)
            col.label(text="sampler is used (can cause artifacts)")


class LUXCORE_RENDER_PT_performance_gpu_devices(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {"LUXCORE"}
    bl_label = "GPU Devices"
    bl_parent_id = "LUXCORE_RENDER_PT_performance"

    @classmethod
    def poll(cls, context):
        config = context.scene.luxcore.config
        return context.scene.render.engine == "LUXCORE" and config.engine == "PATH" and config.device == "OCL"

    def _show_openCL_device_warning(self, context):
        config = context.scene.luxcore.config
        opencl = context.scene.luxcore.opencl
        
        gpu_devices = [device for device in opencl.devices if device.type == "OPENCL_GPU"]
        # We don't show OpenCL CPU devices, we just need them to check if there are other devices
        cpu_devices = [device for device in opencl.devices if device.type == "OPENCL_CPU"]
        other_devices = set(opencl.devices) - (set(gpu_devices) | set(cpu_devices))

        has_gpus = any([device.enabled for device in gpu_devices])
        has_others = any([device.enabled for device in other_devices])

        return (config.engine == "PATH" and config.device == "OCL" and not has_gpus and not has_others)

    def draw_header(self, context):
        layout = self.layout
        if self._show_openCL_device_warning(context):
            layout.label(text="", icon=icons.WARNING)            

    def draw(self, context):
        layout = self.layout
        opencl = context.scene.luxcore.opencl

        layout.use_property_split = True
        layout.use_property_decorate = False

        if not opencl.devices:
            layout.label(text="No OpenCL Devices available.", icon=icons.WARNING)

        layout.operator("luxcore.update_opencl_devices")

        if opencl.devices:
            if self._show_openCL_device_warning(context):
                layout.label(text="Select at least one OpenCL device!", icon=icons.WARNING)

            gpu_devices = [device for device in opencl.devices if device.type == "OPENCL_GPU"] 
            for device in gpu_devices:
                layout.prop(device, "enabled", text=device.name)

