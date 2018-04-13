from .. import LuxCoreNodeMaterial


class LuxCoreNodeMatNull(LuxCoreNodeMaterial):
    bl_label = "Null Material"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Transmission Color", (1, 1, 1))

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def export(self, exporter, props, luxcore_name=None):
        definitions = {
            "type": "null",
        }

        # This is a neat trick to get a colored transparent material:
        # Use a color or texture on the transparency property.
        # We only use it when we need it.
        transparency = self.inputs["Transmission Color"].export(exporter, props)
        if transparency != 1.0 and transparency != [1.0, 1.0, 1.0]:
            definitions["transparency"] = transparency

        return self.base_export(props, definitions, luxcore_name)
