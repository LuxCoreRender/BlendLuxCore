import bpy
from bpy.props import IntProperty, BoolProperty

USE_NOISE_THRESH_DESC = (
    "The rendering will stop when the noise in the image falls "
    "below the specified threshold")

NOISE_THRESH_DESC = (
    "Value between 0 and 255. If the noise falls below this value, the rendering is stopped. "
    "Smaller values mean less noise. "
    "It may be hard to reach a smaller noise value than 3"
)
NOISE_THRESH_WARMUP_DESC = (
    "How many samples to render before doing the first convergence test. "
    "Note that the first actual noise check only happens at the second test, after (warmup + step) samples"
)
NOISE_THRESH_STEP_DESC = (
    "How many samples to render between convergence tests. Use smaller values if "
    "your scene renders very slowly, and higher values if it renders very fast"
)


# Attached to render layer and scene
class LuxCoreHaltConditions(bpy.types.PropertyGroup):
    enable = BoolProperty(name="Enable", default=False)

    use_time = BoolProperty(name="Use Time", default=False)
    time = IntProperty(name="Time (s)", default=600, min=1)

    use_samples = BoolProperty(name="Use Samples", default=False)
    samples = IntProperty(name="Samples", default=500, min=1)

    # Noise threshold
    use_noise_thresh = BoolProperty(name="Use Noise Threshold", default=False,
                                    description=USE_NOISE_THRESH_DESC)
    noise_thresh = IntProperty(name="Noise Threshold", default=5, min=0, soft_min=3, max=255,
                               description=NOISE_THRESH_DESC)
    noise_thresh_warmup = IntProperty(name="Warmup Samples", default=64, min=1,
                                      description=NOISE_THRESH_WARMUP_DESC)
    noise_thresh_step = IntProperty(name="Test Step Samples", default=64, min=1, soft_min=16,
                                    description=NOISE_THRESH_STEP_DESC)

    def is_enabled(self):
        return self.enable and (self.use_time or self.use_samples or self.use_noise_thresh)
