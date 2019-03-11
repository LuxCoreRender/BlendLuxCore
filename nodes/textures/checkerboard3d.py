from .. import LuxCoreNodeTexture
from ... import utils


class LuxCoreNodeTexCheckerboard3D(LuxCoreNodeTexture):
    bl_label = "3D Checkerboard"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color 1", [0.1] * 3)
        self.add_input("LuxCoreSocketColor", "Color 2", [0.6] * 3)
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, props)

        definitions = {
            "type": "checkerboard3d",
            "texture1": self.inputs["Color 1"].export(exporter, props),
            "texture2": self.inputs["Color 2"].export(exporter, props),
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }
        return self.create_props(props, definitions, luxcore_name)
