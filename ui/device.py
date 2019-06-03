# from bl_ui.properties_render import RenderButtonsPanel
# from bpy.types import Panel
# from .. import utils
# from . import icons
#
#
# class LUXCORE_RENDER_PT_device_settings(RenderButtonsPanel, Panel):
#     COMPAT_ENGINES = {"LUXCORE"}
#     bl_label = "LuxCore Device Settings"
#
#     @classmethod
#     def poll(cls, context):
#         return context.scene.render.engine == "LUXCORE"
#
#     def _draw_devices(self, layout, devices):
#         for device in devices:
#             layout.prop(device, "enabled", text=device.name)
#
#     def _draw_cpu_settings(self, layout, context):
#         # CPU settings for native C++ threads
#         row = layout.row(align=True)
#         row.prop(context.scene.render, "threads_mode", expand=True)
#         sub = row.row(align=True)
#         sub.enabled = context.scene.render.threads_mode == 'FIXED'
#         sub.prop(context.scene.render, "threads")
#
#     def _show_hybrid_metropolis_warning(self, context):
#         config = context.scene.luxcore.config
#         opencl = context.scene.luxcore.opencl
#         return (config.engine == "PATH" and config.device == "OCL"
#                 and config.sampler == "METROPOLIS" and opencl.use_native_cpu)
#
#     def draw_header(self, context):
#         if self._show_hybrid_metropolis_warning(context):
#             self.layout.label("", icon=icons.WARNING)
#
#     def draw(self, context):
#         layout = self.layout
#         config = context.scene.luxcore.config
#         opencl = context.scene.luxcore.opencl
#
#         if config.engine == "PATH" and config.device == "OCL":
#             if not utils.is_opencl_build():
#                 # pyluxcore was compiled without OpenCL support
#                 layout.label("No OpenCL support in this BlendLuxCore version", icon=icons.ERROR)
#
#             if not opencl.devices:
#                 layout.label("No OpenCL Devices available.", icon=icons.WARNING)
#                 layout.operator("luxcore.update_opencl_devices")
#
#             gpu_devices = [device for device in opencl.devices if device.type == "OPENCL_GPU"]
#             # We don't show OpenCL CPU devices, we just need them to check if there are other devices
#             cpu_devices = [device for device in opencl.devices if device.type == "OPENCL_CPU"]
#             other_devices = set(opencl.devices) - (set(gpu_devices) | set(cpu_devices))
#
#             box = layout.box()
#             box.label("GPU Devices:")
#             self._draw_devices(box, gpu_devices)
#
#             # This probably never happens
#             if other_devices:
#                 col = layout.column(align=True)
#                 box = col.box()
#                 box.label("Other Devices")
#                 box = col.box()
#                 self._draw_devices(box, other_devices)
#
#             has_gpus = any([device.enabled for device in gpu_devices])
#             has_others = any([device.enabled for device in other_devices])
#             if not has_gpus and not has_others:
#                 layout.label("Select at least one OpenCL device!", icon=icons.WARNING)
#
#             col = layout.column(align=True)
#             col.prop(opencl, "use_native_cpu", toggle=True)
#             if opencl.use_native_cpu:
#                 box = col.box()
#                 self._draw_cpu_settings(box, context)
#
#                 if self._show_hybrid_metropolis_warning(context):
#                     col = box.column(align=True)
#                     col.label("CPU should be disabled if Metropolis", icon=icons.WARNING)
#                     col.label("sampler is used (can cause artifacts)")
#         else:
#             col = layout.column()
#             col.label(text="CPU Threads:")
#             self._draw_cpu_settings(col, context)
