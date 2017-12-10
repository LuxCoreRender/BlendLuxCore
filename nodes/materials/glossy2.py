import bpy
from bpy.props import BoolProperty
from .. import LuxCoreNodeMaterial


class luxcore_material_glossy2(LuxCoreNodeMaterial):
    """Glossy2 material node"""
    bl_label = "Glossy2 Material"
    bl_width_min = 160

    multibounce = BoolProperty(name="Multibounce", default=False)

    def init(self, context):
        self.add_input("LuxCoreSocketColorTex", "Diffuse Color", [0.7] * 3)
        self.add_input("LuxCoreSocketColorTex", "Specular Color", [0.05] * 3)
        self.add_input("LuxCoreSocketColorTex", "Absorption Color", [0] * 3)
        self.add_input("LuxCoreSocketFloatTex", "Absorption Depth", 0)
        # TODO: roughness
        # TODO: IOR (index)

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multibounce")

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "glossy2",
            "kd": self.inputs["Diffuse Color"].export(props),
            "ks": self.inputs["Specular Color"].export(props),
            # "uroughness":
            # "vroughness":
            "ka": self.inputs["Absorption Color"].export(props),
            "d": self.inputs["Absorption Depth"].export(props),
            # "index":
            "multibounce": self.multibounce,
        }
        return self.base_export(props, definitions, luxcore_name)
