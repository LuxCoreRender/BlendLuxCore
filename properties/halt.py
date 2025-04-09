import bpy
from bpy.props import IntProperty, BoolProperty

USE_SAMPLES_DESC = (
    "The rendering will stop when the number of samples reaches "
    "the specified value"
)

SAMPLES_DESC = (
    "At least this many samples will be rendered before stopping"
)

USE_LIGHT_PATH_SAMPLES_DESC = (
    "The rendering will stop when the number of light path samples reaches "
    "the specified value"
)

LIGHT_PATH_SAMPLES_DESC = (
    "At least this many light path samples will be rendered before stopping"
)

USE_NOISE_THRESH_DESC = (
    "The rendering will stop when the noise in the image falls "
    "below the specified threshold"
)

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


# Attached to view layer and scene
class LuxCoreHaltConditions(bpy.types.PropertyGroup):
    enable: BoolProperty(name="Enable", default=False)

    use_time: BoolProperty(name="Use Time", default=False)
    time: IntProperty(name="Time (s)", default=600, min=1)

    use_samples: BoolProperty(name="Use Samples", default=True,
                               description=USE_SAMPLES_DESC)
    samples: IntProperty(name="Samples", default=32, min=2, soft_max=16384, 
                          description=SAMPLES_DESC)

    use_light_samples: BoolProperty(name="Use Light Path Samples", default=False,
                                     description=USE_LIGHT_PATH_SAMPLES_DESC)
    light_samples: IntProperty(name="Light Path Samples", default=100, min=1,
                                description=LIGHT_PATH_SAMPLES_DESC)

    # Noise threshold
    use_noise_thresh: BoolProperty(name="Use Noise Threshold", default=False,
                                    description=USE_NOISE_THRESH_DESC)
    noise_thresh: IntProperty(name="Noise Threshold", default=5, min=0, soft_min=3, max=255,
                               description=NOISE_THRESH_DESC)
    noise_thresh_warmup: IntProperty(name="Warmup Samples", default=64, min=1,
                                      description=NOISE_THRESH_WARMUP_DESC)
    noise_thresh_step: IntProperty(name="Test Step Samples", default=64, min=1, soft_min=16,
                                    description=NOISE_THRESH_STEP_DESC)

    def is_enabled(self):
        return self.enable and (self.use_time or self.use_samples or self.use_noise_thresh)
