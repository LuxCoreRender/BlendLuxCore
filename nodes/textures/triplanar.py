import bpy
from bpy.props import BoolProperty
from ..base import LuxCoreNodeTexture
from ... import utils
from ...utils import node as utils_node



class LuxCoreNodeTriplanar(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Triplanar Mapping"
    bl_width_default = 160

    def update_individual_textures(self, context):
        if self.individual_textures:
            self.inputs["Color"].name = "Color X"
        else:
            self.inputs["Color X"].name = "Color"

        self.inputs["Color Y"].enabled = self.individual_textures
        self.inputs["Color Z"].enabled = self.individual_textures
        utils_node.force_viewport_update(self, context)

    individual_textures: BoolProperty(update=update_individual_textures, name="Individual Textures",
                                      default=False)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", [0.8, 0.0, 0.0])
        self.add_input("LuxCoreSocketColor", "Color Y", [0.0, 0.8, 0.0])
        self.inputs["Color Y"].enabled = False
        self.add_input("LuxCoreSocketColor", "Color Z", [0.0, 0.0, 0.8])
        self.inputs["Color Z"].enabled = False
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "individual_textures")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        mapping_type, uvindex, transformation = self.inputs["3D Mapping"].export(exporter, depsgraph, props)

        if self.individual_textures:
            tex1 = self.inputs["Color X"].export(exporter, depsgraph, props)
            tex2 = self.inputs["Color Y"].export(exporter, depsgraph, props)
            tex3 = self.inputs["Color Z"].export(exporter, depsgraph, props)
        else:
            tex1 = tex2 = tex3 = self.inputs["Color"].export(exporter, depsgraph, props)

        definitions = {
            "type": "triplanar",
            "texture1": tex1,
            "texture2": tex2,
            "texture3": tex3,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }

        if not utils_node.get_link(self.inputs["3D Mapping"]):
            definitions["mapping.type"] = "localmapping3d"

        if mapping_type == "uvmapping3d":
            definitions["mapping.uvindex"] = uvindex

        return self.create_props(props, definitions, luxcore_name)
