from .. import LuxCoreNodeTexture


class LuxCoreNodeTexRemap(LuxCoreNodeTexture):
    bl_label = "Remap"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value", 0.5)
        self.add_input("LuxCoreSocketFloatUnbounded", "Source Min", 0)
        self.add_input("LuxCoreSocketFloatUnbounded", "Source Max", 1)
        self.add_input("LuxCoreSocketFloatUnbounded", "Target Min", 0)
        self.add_input("LuxCoreSocketFloatUnbounded", "Target Max", 1)

        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "remap",
            "value": self.inputs["Value"].export(exporter, props),
            "sourcemin": self.inputs["Source Min"].export(exporter, props),
            "sourcemax": self.inputs["Source Max"].export(exporter, props),
            "targetmin": self.inputs["Target Min"].export(exporter, props),
            "targetmax": self.inputs["Target Max"].export(exporter, props),
        }
        return self.create_props(props, definitions, luxcore_name)
