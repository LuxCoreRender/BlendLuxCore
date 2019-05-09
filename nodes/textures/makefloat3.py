from .. import LuxCoreNodeTexture


class LuxCoreNodeTexMakeFloat3(LuxCoreNodeTexture):
    bl_label = "Combine RGB"
    bl_width_default = 130

    def init(self, context):
        self.add_input("LuxCoreSocketFloat0to1", "R", 0)
        self.add_input("LuxCoreSocketFloat0to1", "G", 0)
        self.add_input("LuxCoreSocketFloat0to1", "B", 0)
        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "makefloat3",
            "texture1": self.inputs[0].export(exporter, props),
            "texture2": self.inputs[1].export(exporter, props),
            "texture3": self.inputs[2].export(exporter, props),
        }

        return self.create_props(props, definitions, luxcore_name)
