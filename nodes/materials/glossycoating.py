import bpy
from bpy.props import BoolProperty
from .. import LuxCoreNodeMaterial, Roughness
from ...utils import node as utils_node


class LuxCoreNodeMatGlossyCoating(LuxCoreNodeMaterial):
    bl_label = "Glossy Coating Material"
    bl_width_default = 160

    multibounce = BoolProperty(name="Multibounce", default=False)
    use_anisotropy = BoolProperty(name=Roughness.aniso_name,
                                  default=False,
                                  description=Roughness.aniso_desc,
                                  update=Roughness.update_anisotropy)

    def init(self, context):
        self.add_input("LuxCoreSocketMaterial", "Base Material")
        self.add_input("LuxCoreSocketColor", "Specular Color", [0.05] * 3)
        self.add_input("LuxCoreSocketColor", "Absorption Color", [0] * 3)
        self.add_input("LuxCoreSocketFloatPositive", "Absorption Depth (nm)", 0)
        Roughness.init(self, 0.05)
        # TODO: IOR (index)
        self.add_common_inputs()
        # glossycoating does not support the transparency property
        self.inputs["Opacity"].enabled = False

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multibounce")
        Roughness.draw(self, context, layout)

    def export(self, props, luxcore_name=None):
        base = utils_node.export_material_input(self.inputs["Base Material"], props)

        definitions = {
            "type": "glossycoating",
            "base": base,
            "ks": self.inputs["Specular Color"].export(props),
            "ka": self.inputs["Absorption Color"].export(props),
            "d": self.inputs["Absorption Depth (nm)"].export(props),
            # "index":
            "multibounce": self.multibounce,
        }
        Roughness.export(self, props, definitions)
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
