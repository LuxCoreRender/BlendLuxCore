from bpy.props import IntProperty, BoolProperty, FloatProperty
from .. import LuxCoreNodeVolume, COLORDEPTH_DESC


class LuxCoreNodeVolHomogeneous(LuxCoreNodeVolume):
    bl_label = "Homogeneous Volume"
    bl_width_min = 160

    # TODO: get name, default, description etc. from super class or something
    priority = IntProperty(name="Priority", default=0, min=0)
    emission_id = IntProperty(name="Lightgroup ID", default=0, min=0)
    color_depth = FloatProperty(name="Absorption Depth", default=1.0, subtype="DISTANCE", unit="LENGTH",
                               description=COLORDEPTH_DESC)

    multiscattering = BoolProperty(name="Multiscattering", default=False)

    def init(self, context):
        self.add_common_inputs()
        self.add_input("LuxCoreSocketColor", "Scattering", (1, 1, 1))
        self.add_input("LuxCoreSocketFloatVector", "Asymmetry", (0, 0, 0))

        self.outputs.new("LuxCoreSocketVolume", "Volume")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multiscattering")
        self.draw_common_buttons(context, layout)

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "homogeneous",
            "scattering": self.inputs["Scattering"].export(props),
            "asymmetry": self.inputs["Asymmetry"].export(props),
            "multiscattering": self.multiscattering,
        }
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
