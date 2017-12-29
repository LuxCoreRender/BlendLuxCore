import bpy
from bpy.props import BoolProperty
from .. import LuxCoreNodeMaterial, Roughness


class LuxCoreNodeMatGlossy2(LuxCoreNodeMaterial):
    bl_label = "Glossy Material"
    bl_width_min = 160

    multibounce = BoolProperty(name="Multibounce", default=False)
    use_anisotropy = BoolProperty(name=Roughness.aniso_name,
                                  default=False,
                                  description=Roughness.aniso_desc,
                                  update=Roughness.update_anisotropy)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Diffuse Color", [0.7] * 3)
        self.add_input("LuxCoreSocketColor", "Specular Color", [0.05] * 3)
        self.add_input("LuxCoreSocketColor", "Absorption Color", [0] * 3)
        self.add_input("LuxCoreSocketFloatPositive", "Absorption Depth (nm)", 0)
        Roughness.init(self, 0.05)
        # TODO: IOR (index)
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multibounce")
        Roughness.draw(self, context, layout)

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "glossy2",
            "kd": self.inputs["Diffuse Color"].export(props),
            "ks": self.inputs["Specular Color"].export(props),
            "ka": self.inputs["Absorption Color"].export(props),
            "d": self.inputs["Absorption Depth (nm)"].export(props),
            # "index":
            "multibounce": self.multibounce,
        }
        Roughness.export(self, props, definitions)
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
