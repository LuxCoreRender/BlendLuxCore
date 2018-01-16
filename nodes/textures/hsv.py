from .. import LuxCoreNodeTexture


class LuxCoreNodeTexHSV(LuxCoreNodeTexture):
    bl_label = "Hue Saturation Value"

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", [1, 1, 1])
        self.add_input("LuxCoreSocketFloat0to1", "Hue", 0.5)
        self.add_input("LuxCoreSocketFloat0to2", "Saturation", 1)
        self.add_input("LuxCoreSocketFloat0to2", "Value", 1)

        self.outputs.new("LuxCoreSocketColor", "Color")

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "hsv",
            "texture": self.inputs["Color"].export(props),
            "hue": self.inputs["Hue"].export(props),
            "saturation": self.inputs["Saturation"].export(props),
            "value": self.inputs["Value"].export(props),
        }
        return self.base_export(props, definitions, luxcore_name)
