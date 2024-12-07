import bpy
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty
from .. import utils
import pyluxcore

class LuxCoreViewportSettings(bpy.types.PropertyGroup):
    halt_time: IntProperty(name="Halt Time (s)", default=10, min=1,
                            description="How long to render in the viewport. "
                                        "When this time is reached, the render is paused")

    devices = [
        ("CPU", "CPU", "Low latency, but slower rendering than on GPU", 0),
        ("OCL", "GPU", "High latency, but faster rendering than on CPU", 1),
    ]
    device: EnumProperty(name="Device", items=devices, default="CPU")

    pixel_sizes = [
        ("1", "1x", "Use the native resolution of the monitor (1 rendered pixel = 1 displayed pixel)", 0),
        ("2", "2x", "Use half the resolution of the monitor (1 rendered pixel = 2x2 displayed pixels)", 1),
        ("4", "4x", "1 rendered pixel = 4x4 displayed pixels", 2),
        ("8", "8x", "1 rendered pixel = 8x8 displayed pixels", 3),
    ]
    pixel_size: EnumProperty(name="Pixel Size", items=pixel_sizes, default="1",
                              description="Scale factor for rendered pixels")

    mag_filters = [
        ("NEAREST", "Nearest (blocky)", "", 0),
        ("LINEAR", "Linear (smooth)", "", 1),
    ]
    mag_filter: EnumProperty(name="Filter", items=mag_filters, default="NEAREST",
                              description="Upscaling filter used when pixel size is larger than 1")

    reduce_resolution_on_edit: BoolProperty(name="Reduce first sample resolution", default=True,
                                             description="Render the first sample after editing the scene "
                                                         "with reduced resolution to provide a quicker response "
                                                         "(does not work when light tracing or bidir are used "
                                                         "for viewport rendering)")
    resolution_reduction: IntProperty(name="Block Size", default=4, min=2,
                                       description="Size of the startup blocks in pixels. A size of 4 means that "
                                                   "one sample is spread over 4x4 pixels on startup")

    use_bidir: BoolProperty(name="Use Bidir", default=True,
                             description="Enable if your scene requires Bidir for complex light paths and "
                                         "you need to preview them in the viewport render. If disabled, "
                                         "the RT Path engine is used in the viewport, which is optimized "
                                         "for quick feedback but can't handle complex light paths")
    add_light_tracing: BoolProperty(name="Add Light Tracing", default=True,
                                    description="Add light tracing in viewport. If disabled, "
                                         "the RT Path engine is used in the viewport, which is optimized "
                                         "for quick feedback but can't handle complex light paths")

    use_denoiser: BoolProperty(name="Denoise", default=True,
                           description="Denoise the viewport render once the halt time is reached. "
                                       "Note that this disables most imagepipeline plugins in the viewport")
    denoisers = [
        ("OIDN", "Intel Open Image Denoiser", "Denoising is only performed once the viewport render pauses", 0),
        ("OPTIX", "OptiX", "Denoises continuously during viewport rendering", 1),
    ]
    denoiser: EnumProperty(name="Denoiser", items=denoisers, default="OPTIX")
    min_samples: IntProperty(name="Min. Samples", default=1, min=0, 
                             description="Minimum amount of samples to be rendered before viewport denoiser is enabled")

    @staticmethod
    def can_use_optix_denoiser(context):
        preferences = utils.get_addon_preferences(context)
        optix_available = False
        # TODO Do we need to check here if the film device supports OptiX?
        
        if preferences.gpu_backend == "CUDA" and preferences.film_device != "none":
            data = pyluxcore.GetOpenCLDeviceDescs()
            prefix = 'opencl.device.' + preferences.film_device

            if data.Get(prefix + ".cuda.compute.major").GetInt() >= 5:
                optix_available = True

        return optix_available

    def get_denoiser(self, context):
        if not self.use_denoiser:
            return None
        if self.can_use_optix_denoiser(context):
            # It's possible that either OptiX or OIDN is used, depending on user choice
            return self.denoiser
        # OptiX can't be used, so OIDN is the only option left
        return "OIDN"
