from .. import LuxCoreNodeMaterial


class LuxCoreNodeMatDisney(LuxCoreNodeMaterial):
    bl_label = "Disney Material"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Base Color", [0.7] * 3)
        self.add_input("LuxCoreSocketFloat0to1", "Subsurface", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Metallic", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Specular", 0.5)
        self.add_input("LuxCoreSocketFloat0to1", "Specular Tint", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Roughness", 0.2)
        self.add_input("LuxCoreSocketFloat0to1", "Anisotropic", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Sheen", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Sheen Tint", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Clearcoat", 0)
        self.add_input("LuxCoreSocketFloat0to1", "Clearcoat Gloss", 1)
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "disney",
            "basecolor": self.inputs["Base Color"].export(exporter, props),
            "subsurface": self.inputs["Subsurface"].export(exporter, props),
            "metallic": self.inputs["Metallic"].export(exporter, props),
            "specular": self.inputs["Specular"].export(exporter, props),
            "speculartint": self.inputs["Specular Tint"].export(exporter, props),
            "roughness": self.inputs["Roughness"].export(exporter, props),
            "anisotropic": self.inputs["Anisotropic"].export(exporter, props),
            "sheen": self.inputs["Sheen"].export(exporter, props),
            "sheentint": self.inputs["Sheen Tint"].export(exporter, props),
            "clearcoat": self.inputs["Clearcoat"].export(exporter, props),
            "clearcoatgloss": self.inputs["Clearcoat Gloss"].export(exporter, props),
        }

        self.export_common_inputs(exporter, props, definitions)
        return self.create_props(props, definitions, luxcore_name)
