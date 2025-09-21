import bpy
from bpy.props import EnumProperty
from .. import icons
from .. import utils
from ..utils import ui as utils_ui
from .utils import use_cycles_settings

TOTAL_QUESTIONS = 3


@utils.count_index
def question(layout, text, index=1):
    layout.label(text=f"({index}/{TOTAL_QUESTIONS}) {text}")


class LUXCORE_OT_render_settings_helper(bpy.types.Operator):
    bl_idname = "luxcore.render_settings_helper"
    bl_label = "Render Settings Helper"
    bl_description = "Interactive render settings guide"
    bl_options = {"UNDO"}

    yes_no_items = [
        ("NOT_SET", "Please Choose", "", 0),
        ("YES", "Yes", "", 1),
        ("NO", "No", "", 2),
    ]

    use_cycles_settings: EnumProperty(items=yes_no_items)

    env_visibility_items = [
        ("NOT_SET", "Please Choose", "", 0),
        (
            "INDOORS",
            "Indoors",
            "Choose this if the world background is only visible through small openings like windows",
            1,
        ),
        (
            "OUTDOORS",
            "Outdoors or Studio",
            "Choose this if the world background is unobstructed",
            2,
        ),
    ]
    env_visibility: EnumProperty(items=env_visibility_items)

    has_caustics: EnumProperty(items=yes_no_items)
    has_SDS_caustics: EnumProperty(items=yes_no_items)

    def _use_GPU(self):
        return (
            utils.luxutils.is_opencl_build() or utils.luxutils.is_cuda_build()
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=450)

    def execute(self, context):
        settings = context.scene.luxcore
        config = settings.config

        # Stuff that's independent from user choices
        config.engine = "PATH"
        config.sampler = "SOBOL"
        config.sampler_gpu = "SOBOL"
        config.sobol_adaptive_strength = 0.9

        if self._use_GPU():
            config.device = "OCL"
        else:
            config.device = "CPU"

        settings.denoiser.enabled = True
        settings.denoiser.type = "OIDN"

        # Evaluate user choices
        if self.use_cycles_settings == "YES":
            use_cycles_settings()

        # Env. light visibility and indirect light speedup
        config.envlight_cache.enabled = self.env_visibility == "INDOORS"
        config.photongi.enabled = self.env_visibility == "INDOORS"
        config.photongi.indirect_enabled = self.env_visibility == "INDOORS"

        # Caustics
        config.path.hybridbackforward_enable = self.has_caustics == "YES"

        # Caustic cache
        if self.has_SDS_caustics == "YES":
            config.photongi.enabled = True
            config.photongi.caustic_enabled = True
            # Disable radius shrinking
            config.photongi.caustic_updatespp_minradius = (
                config.photongi.caustic_lookup_radius
            )

        utils_ui.tag_region_for_redraw(context, "PROPERTIES", "WINDOW")
        return {"FINISHED"}

    def _show_result(self, text):
        layout = self.layout
        row = layout.row(align=True)
        row.label(text="", icon=icons.GREEN_RHOMBUS)
        row.label(text=text)

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        question.index = 1

        # Should Cycles settings be ported?
        question(layout, "Should Cycles settings and shaders be used?")
        layout.prop(self, "use_cycles_settings", expand=True)

        if self.use_cycles_settings == "NOT_SET":
            layout.separator()
            return

        if self.use_cycles_settings == "YES":
            self._show_result(
                "Will use Cycles settings for materials, lights and world"
            )

        # Is the environment light obscured or not, is indirect light likely noisy or not?
        question(layout, "Is your scene indoors or outdoors?")
        layout.prop(self, "env_visibility", expand=True)

        if self.env_visibility == "NOT_SET":
            layout.separator()
            return

        if self.env_visibility == "INDOORS":
            self._show_result("Will enable PhotonGI Indirect Cache")
            self._show_result("Will enable Environment Light Cache")
        else:
            self._show_result(
                "Indirect and environment light caches not needed"
            )

        # Caustics
        question(layout, "Are there caustics in your scene?")
        layout.prop(self, "has_caustics", expand=True)

        if self.has_caustics == "NOT_SET":
            layout.separator()
            return

        if self.has_caustics == "YES":
            self._show_result('Will enable "Add Light Tracing" option')
        else:
            self._show_result('"Add Light Tracing" not needed')

        if self.has_caustics == "YES":
            # SDS caustics
            layout.label(
                text="Are the caustics visible in a mirror, or are the viewed through glass (e.g. in a pool)?"
            )
            layout.prop(self, "has_SDS_caustics", expand=True)

            if self.has_SDS_caustics == "NOT_SET":
                layout.separator()
                return

            if self.has_SDS_caustics == "YES":
                self._show_result("Will enable PhotonGI Caustic Cache")
                col = layout.column(align=True)
                col.label(
                    text="What would be a good photon radius for your scene size? (in meters)"
                )
                col.label(
                    text="(Too large values will look blurred, too small values will create noise)"
                )
                col.prop(config.photongi, "caustic_lookup_radius")
            else:
                self._show_result("Caustic cache not needed")

        # Show general settings that will be used
        layout.separator()
        layout.label(text="Additionally, these general settings will be set:")
        self._show_result("Engine: Path")
        self._show_result(f'Device: {"GPU" if self._use_GPU() else "CPU"}')
        self._show_result("Sampler: Sobol (adaptive)")
        self._show_result("Denoiser: enabled")
