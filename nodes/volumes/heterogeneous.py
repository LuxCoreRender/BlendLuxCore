import math
import bpy
from bpy.props import IntProperty, BoolProperty, FloatProperty, PointerProperty, StringProperty
from .. import LuxCoreNodeVolume, COLORDEPTH_DESC
from ... import utils
from ...properties.light import LIGHTGROUP_DESC
from ...ui import icons


STEP_SIZE_DESCRIPTION = (
    "Used to specify the granularity of the volume sampling steps. "
    "If the step size is too large, artifacts will appear. "
    "If it is too small, the rendering will be much slower"
)

MULTISCATTERING_DESC = (
    "Simulate multiple scattering events per ray. "
    "Makes volumes with high scattering scale appear more realistic, "
    "but leads to slower rendering performance"
)


class LuxCoreNodeVolHeterogeneous(LuxCoreNodeVolume):
    bl_label = "Heterogeneous Volume"
    bl_width_default = 190

    # TODO: get name, default, description etc. from super class or something
    priority = IntProperty(name="Priority", default=0, min=0)
    color_depth = FloatProperty(name="Absorption Depth", default=1.0, min=0,
                                subtype="DISTANCE", unit="LENGTH",
                                description=COLORDEPTH_DESC)
    lightgroup = StringProperty(name="Light Group", description=LIGHTGROUP_DESC)

    step_size = FloatProperty(name="Step Size", default=0.1, min=0.0001,
                              soft_min=0.01, soft_max=1,
                              subtype="DISTANCE", unit="LENGTH",
                              description=STEP_SIZE_DESCRIPTION)
    maxcount = IntProperty(name="Max. Steps", default=1024, min=0,
                           description="Maximum Step Count for Volume Integration")
    auto_step_settings = BoolProperty(name="Auto Step Settings", default=False,
                                      description="Enable when using a smoke domain. "
                                                  "Automatically calculates the correct step size and maximum steps")

    def poll_domain(self, obj):
        # Only allow objects with a smoke modifier in domain mode to be picked
        return utils.find_smoke_domain_modifier(obj)

    domain = PointerProperty(name="Domain", type=bpy.types.Object, poll=poll_domain,
                             description="Domain object for calculating the step size and maximum steps settings")

    multiscattering = BoolProperty(name="Multiscattering", default=False,
                                   description=MULTISCATTERING_DESC)

    def init(self, context):
        self.add_common_inputs()
        self.add_input("LuxCoreSocketColor", "Scattering", (1, 1, 1))
        self.add_input("LuxCoreSocketFloatPositive", "Scattering Scale", 1.0)
        self.add_input("LuxCoreSocketVolumeAsymmetry", "Asymmetry", (0, 0, 0))

        self.outputs.new("LuxCoreSocketVolume", "Volume")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multiscattering")

        layout.prop(self, "auto_step_settings")
        if self.auto_step_settings:
            layout.prop(self, "domain")

            if self.domain and not utils.find_smoke_domain_modifier(self.domain):
                layout.label("Not a smoke domain!", icon=icons.WARNING)
            elif self.domain is None:
                layout.label("Select the smoke domain object", icon=icons.WARNING)
        else:
            layout.prop(self, "step_size")
            layout.prop(self, "maxcount")

        self.draw_common_buttons(context, layout)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "heterogeneous",
            "asymmetry": self.inputs["Asymmetry"].export(exporter, props),
            "multiscattering": self.multiscattering,
        }

        if self.auto_step_settings and self.domain:
            # Search smoke domain target for smoke modifiers
            smoke_domain_mod = utils.find_smoke_domain_modifier(self.domain)

            if smoke_domain_mod is None:
                msg = 'Object "%s" is not a smoke domain' % self.domain.name
                raise Exception(msg)

            settings = smoke_domain_mod.domain_settings
            # A list with 3 elements (resolution in x, y, z directions)
            resolutions = list(settings.domain_resolution)
            if settings.use_high_resolution:
                resolutions = [res * (settings.amplify + 1) for res in resolutions]

            worldscale = utils.get_worldscale(exporter.scene, as_scalematrix=False)
            dimensions = [dim * worldscale for dim in self.domain.dimensions]
            # The optimal step size on each axis
            step_sizes = [dim / res for dim, res in zip(dimensions, resolutions)]
            # Use the smallest step size in LuxCore
            step_size = min(step_sizes)
            definitions["steps.size"] = step_size

            # Find the max. count required in the worst case
            diagonal = self.domain.dimensions.length * worldscale
            worst_case_maxcount = math.ceil(diagonal / step_size)
            definitions["steps.maxcount"] = worst_case_maxcount

            print('INFO: "%s" in volume node tree "%s" Auto Step Settings:' % (self.name, self.id_data.name))
            print("  Using steps.size = %.3f m" % step_size)
            print("  Using steps.maxcount =", worst_case_maxcount)
        else:
            definitions["steps.size"] = self.step_size
            definitions["steps.maxcount"] = self.maxcount

        self.export_common_inputs(exporter, props, definitions)
        return self.create_props(props, definitions, luxcore_name)
