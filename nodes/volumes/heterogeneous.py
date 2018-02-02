from bpy.props import IntProperty, BoolProperty, FloatProperty
from .. import utils
from .. import LuxCoreNodeVolume, COLORDEPTH_DESC


STEP_SIZE_DESCRIPTION = (
    "Used to specify the granularity of the volume sampling steps. "
    "If the step size is too large, artifacts will appear. "
    "If it is too small, the rendering will be much slower"
)

MULTISCATTERING_DESC = (
    "Simulate multiple scattering events per ray. "
    "Makes volumes with high scattering scale appear more realistic, "
    "but leads to slower rendering performance."
)


class LuxCoreNodeVolHeterogeneous(LuxCoreNodeVolume):
    bl_label = "Heterogeneous Volume"
    bl_width_min = 160

    # TODO: get name, default, description etc. from super class or something
    priority = IntProperty(name="Priority", default=0, min=0)
    emission_id = IntProperty(name="Lightgroup ID", default=0, min=0)
    color_depth = FloatProperty(name="Absorption Depth", default=1.0, min=0,
                                subtype="DISTANCE", unit="LENGTH",
                                description=COLORDEPTH_DESC)
    step_size = FloatProperty(name="Step Size", default=0.1, min=0.0001,
                              soft_min=0.01, soft_max=1,
                              subtype="DISTANCE", unit="LENGTH",
                              description=STEP_SIZE_DESCRIPTION)
    maxcount = IntProperty(name="Max. Step Count", default=1024, min=0,
                           description="Maximum Step Count for Volume Integration")

    multiscattering = BoolProperty(name="Multiscattering", default=False,
                                   description=MULTISCATTERING_DESC)

    def init(self, context):
        self.add_common_inputs()
        self.add_input("LuxCoreSocketColor", "Scattering", (1, 1, 1))
        self.add_input("LuxCoreSocketFloatPositive", "Scattering Scale", 1.0)
        self.add_input("LuxCoreSocketFloatVector", "Asymmetry", (0, 0, 0))

        self.outputs.new("LuxCoreSocketVolume", "Volume")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multiscattering")
        layout.prop(self, "step_size")
        layout.prop(self, "maxcount")
        self.draw_common_buttons(context, layout)

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "heterogeneous",
            "steps.size": self.step_size,
            "steps.maxcount": self.maxcount,
            "asymmetry": self.inputs["Asymmetry"].export(props),
            "multiscattering": self.multiscattering,
        }
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
