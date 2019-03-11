import bpy
from bpy.props import BoolProperty
from .. import LuxCoreNodeMaterial, Roughness
from .glossytranslucent import IOR_DESCRIPTION


class LuxCoreNodeMatGlossy2(LuxCoreNodeMaterial):
    bl_label = "Glossy Material"
    bl_width_default = 160

    def update_use_ior(self, context):
        self.inputs["IOR"].enabled = self.use_ior
        self.inputs["Specular Color"].enabled = not self.use_ior

    multibounce = BoolProperty(name="Multibounce", default=False)
    use_ior = BoolProperty(name="Use IOR", default=False,
                           update=update_use_ior,
                           description=IOR_DESCRIPTION)
    use_anisotropy = BoolProperty(name=Roughness.aniso_name,
                                  default=False,
                                  description=Roughness.aniso_desc,
                                  update=Roughness.update_anisotropy)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Diffuse Color", [0.7] * 3)
        self.add_input("LuxCoreSocketColor", "Specular Color", [0.05] * 3)
        self.add_input("LuxCoreSocketIOR", "IOR", 1.5)
        self.inputs["IOR"].enabled = False
        self.add_input("LuxCoreSocketColor", "Absorption Color", [0] * 3)
        self.add_input("LuxCoreSocketFloatPositive", "Absorption Depth (nm)", 0)
        Roughness.init(self, 0.05)
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multibounce")
        layout.prop(self, "use_ior")
        Roughness.draw(self, context, layout)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "glossy2",
            "kd": self.inputs["Diffuse Color"].export(exporter, props),
            "ka": self.inputs["Absorption Color"].export(exporter, props),
            "d": self.inputs["Absorption Depth (nm)"].export(exporter, props),
            "multibounce": self.multibounce,
        }

        if self.use_ior:
            definitions["index"] = self.inputs["IOR"].export(exporter, props)
            definitions["ks"] = [1, 1, 1]
        else:
            definitions["ks"] = self.inputs["Specular Color"].export(exporter, props)

        Roughness.export(self, exporter, props, definitions)
        self.export_common_inputs(exporter, props, definitions)
        return self.create_props(props, definitions, luxcore_name)
