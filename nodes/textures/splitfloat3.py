from .. import LuxCoreNodeTexture


class LuxCoreNodeTexSplitFloat3(LuxCoreNodeTexture):
    bl_label = "Split RGB"
    bl_width_default = 100

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", (1, 1, 1))
        self.outputs.new("LuxCoreSocketFloatUnbounded", "R")
        self.outputs.new("LuxCoreSocketFloatUnbounded", "G")
        self.outputs.new("LuxCoreSocketFloatUnbounded", "B")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        if output_socket == self.outputs["R"]:
            channel = 0
        elif output_socket == self.outputs["G"]:
            channel = 1
        elif output_socket == self.outputs["B"]:
            channel = 2
        else:
            raise Exception("Unknown output socket in splitfloat3 texture")

        definitions = {
            "type": "splitfloat3",
            "texture": self.inputs[0].export(exporter, props),
            "channel": channel,
        }

        return self.create_props(props, definitions, luxcore_name)
