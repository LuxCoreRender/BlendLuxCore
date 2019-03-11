from bpy.props import IntProperty, BoolProperty, FloatProperty, StringProperty
from .. import LuxCoreNodeVolume, COLORDEPTH_DESC
from ...properties.light import LIGHTGROUP_DESC


class LuxCoreNodeVolHomogeneous(LuxCoreNodeVolume):
    bl_label = "Homogeneous Volume"
    bl_width_default = 175

    # TODO: get name, default, description etc. from super class or something
    priority = IntProperty(name="Priority", default=0, min=0)
    color_depth = FloatProperty(name="Absorption Depth", default=1.0, min=0,
                                subtype="DISTANCE", unit="LENGTH",
                                description=COLORDEPTH_DESC)
    lightgroup = StringProperty(name="Light Group", description=LIGHTGROUP_DESC)

    multiscattering = BoolProperty(name="Multiscattering", default=False)

    def init(self, context):
        self.add_common_inputs()
        self.add_input("LuxCoreSocketColor", "Scattering", (1, 1, 1))
        self.add_input("LuxCoreSocketFloatPositive", "Scattering Scale", 1.0)
        self.add_input("LuxCoreSocketVolumeAsymmetry", "Asymmetry", (0, 0, 0))

        self.outputs.new("LuxCoreSocketVolume", "Volume")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multiscattering")
        self.draw_common_buttons(context, layout)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "homogeneous",
            "asymmetry": self.inputs["Asymmetry"].export(exporter, props),
            "multiscattering": self.multiscattering,
        }        
        self.export_common_inputs(exporter, props, definitions)
        return self.create_props(props, definitions, luxcore_name)
