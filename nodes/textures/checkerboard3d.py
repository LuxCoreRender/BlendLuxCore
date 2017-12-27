from .. import LuxCoreNodeTexture
from ... import utils


class LuxCoreNodeTexCheckerboard3D(LuxCoreNodeTexture):
    bl_label = "3D Checkerboard"
    bl_width_min = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color 1", [0.1] * 3)
        self.add_input("LuxCoreSocketColor", "Color 2", [0.6] * 3)
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def export(self, props, luxcore_name=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(props)

        definitions = {
            "type": "checkerboard3d",
            "texture1": self.inputs["Color 1"].export(props),
            "texture2": self.inputs["Color 2"].export(props),
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation),
        }
        return self.base_export(props, definitions, luxcore_name)
