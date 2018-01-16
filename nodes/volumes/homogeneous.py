from bpy.props import IntProperty, BoolProperty, FloatProperty
from .. import LuxCoreNodeVolume, COLORDEPTH_DESC
from .. import utils


class LuxCoreNodeVolHomogeneous(LuxCoreNodeVolume):
    bl_label = "Homogeneous Volume"
    bl_width_min = 160

    # TODO: get name, default, description etc. from super class or something
    priority = IntProperty(name="Priority", default=0, min=0)
    emission_id = IntProperty(name="Lightgroup ID", default=0, min=0)
    color_depth = FloatProperty(name="Absorption Depth", default=1.0, min=0,
                                subtype="DISTANCE", unit="LENGTH",
                                description=COLORDEPTH_DESC)

    multiscattering = BoolProperty(name="Multiscattering", default=False)

    def init(self, context):
        self.add_common_inputs()
        self.add_input("LuxCoreSocketColor", "Scattering", (1, 1, 1))
        self.add_input("LuxCoreSocketFloatPositive", "Scattering Scale", 1.0)
        self.add_input("LuxCoreSocketFloatVector", "Asymmetry", (0, 0, 0))

        self.outputs.new("LuxCoreSocketVolume", "Volume")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multiscattering")
        self.draw_common_buttons(context, layout)

    def export(self, props, luxcore_name=None):
        scatter_col = self.inputs["Scattering"].export(props)
        
        # Implicitly create a scale texture with unique name
        tex_name = self.make_name() + "_scale"
        helper_prefix = "scene.textures." + tex_name + "."
        helper_defs = {
            "type": "scale",
            "texture1": self.inputs["Scattering Scale"].export(props),
            "texture2": self.inputs["Scattering"].export(props),
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))
        scatter_col = tex_name

        definitions = {
            "type": "homogeneous",
            "scattering": scatter_col,
            "asymmetry": self.inputs["Asymmetry"].export(props),
            "multiscattering": self.multiscattering,
        }        
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
