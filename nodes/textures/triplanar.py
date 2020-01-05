import bpy
from ..base import LuxCoreNodeTexture
from ... import utils



class LuxCoreNodeTriplanar(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Triplanar Mapping"
    bl_width_default = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Texture 1", [0.8, 0.0, 0.0])
        self.add_input("LuxCoreSocketColor", "Texture 2", [0.0, 0.8, 0.0])
        self.add_input("LuxCoreSocketColor", "Texture 3", [0.0, 0.0, 0.8])
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        mapping_type, uvindex, transformation = self.inputs["3D Mapping"].export(exporter, depsgraph, props)

        definitions = {
            "type": "triplanar",
            "texture1": self.inputs["Texture 1"].export(exporter, depsgraph, props),
            "texture2": self.inputs["Texture 2"].export(exporter, depsgraph, props),
            "texture3": self.inputs["Texture 3"].export(exporter, depsgraph, props),

            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }

        if not self.inputs["3D Mapping"].is_linked:
            definitions.update({
                "mapping.type": "localmapping3d",
            })

        if mapping_type == "uvmapping3d":
            definitions["mapping.uvindex"] = uvindex

        return self.create_props(props, definitions, luxcore_name)
