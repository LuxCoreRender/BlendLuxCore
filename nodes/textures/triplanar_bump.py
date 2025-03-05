import bpy
from bpy.props import BoolProperty, FloatProperty
from ..base import LuxCoreNodeTexture, LuxCoreNodeMaterial
from ... import utils
from ...utils import node as utils_node
from .bump import SAMPLING_DISTANCE_DESC


class LuxCoreNodeTexTriplanarBump(LuxCoreNodeTexture, bpy.types.Node):
    bl_label = "Triplanar Bump Mapping"
    bl_width_default = 200

    def update_multiple_textures(self, context):
        if self.multiple_textures:
            self.inputs["Value"].name = "Value X"
            self.inputs["Bump Height"].name = "Bump Height X"
        else:
            self.inputs["Value X"].name = "Value"
            self.inputs["Bump Height X"].name = "Bump Height"

        id = self.inputs.find("Value Y")
        self.inputs[id].enabled = self.multiple_textures
        id = self.inputs.find("Bump Height Y")
        self.inputs[id].enabled = self.multiple_textures
        id = self.inputs.find("Value Z")
        self.inputs[id].enabled = self.multiple_textures
        id = self.inputs.find("Bump Height Z")
        self.inputs[id].enabled = self.multiple_textures
        
        utils_node.force_viewport_update(self, context)

    multiple_textures: BoolProperty(update=update_multiple_textures, name="Multiple Textures", default=False,
                                    description="Makes it possible to assign textures to each axis individually")

    # Note: exported in the export_common_inputs() method of material nodes
    sampling_distance: FloatProperty(name="Sampling Distance",
                                     default=0.001, min=0.000001, soft_max=0.001, step=0.00001,
                                     subtype="DISTANCE",
                                     description=SAMPLING_DISTANCE_DESC,
                                     update=utils_node.force_viewport_update)

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value", 0)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height", 0.001)
        self.add_input("LuxCoreSocketFloatUnbounded", "Value Y", 0, enabled=False)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height Y", 0.001, enabled=False)
        self.add_input("LuxCoreSocketFloatUnbounded", "Value Z", 0, enabled=False)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height Z", 0.001, enabled=False)
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketBump", "Bump")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multiple_textures")

        col = layout.column()
        output = self.outputs["Bump"]
        col.active = output.is_linked and isinstance(output.links[0].to_node, LuxCoreNodeMaterial)
        col.prop(self, "sampling_distance")

    def _create_bump_tex(self, suffix, value, height, props):
        tex_name = self.make_name() + suffix
        prefix = "scene.textures." + tex_name + "."
        defs = {
            "type": "scale",
            "texture1": value,
            "texture2": height,
        }
        props.Set(utils.create_props(prefix, defs))
        return tex_name

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        if self.multiple_textures:
            value1 = self.inputs["Value X"].export(exporter, depsgraph, props)
            height1 = self.inputs["Bump Height X"].export(exporter, depsgraph, props)
            tex1 = self._create_bump_tex("bumpX", value1, height1, props)

            value2 = self.inputs["Value Y"].export(exporter, depsgraph, props)
            height2 = self.inputs["Bump Height Y"].export(exporter, depsgraph, props)
            tex2 = self._create_bump_tex("bumpY", value2, height2, props)

            value3 = self.inputs["Value Z"].export(exporter, depsgraph, props)
            height3 = self.inputs["Bump Height Z"].export(exporter, depsgraph, props)
            tex3 = self._create_bump_tex("bumpZ", value3, height3, props)
        else:
            value = self.inputs["Value"].export(exporter, depsgraph, props)
            height = self.inputs["Bump Height"].export(exporter, depsgraph, props)
            tex1 = tex2 = tex3 = self._create_bump_tex("bump", value, height, props)

        definitions = {
            "type": "triplanar",
            "texture1": tex1,
            "texture2": tex2,
            "texture3": tex3,
        }
        definitions.update(self.inputs["3D Mapping"].export(exporter, depsgraph, props))

        if not utils_node.get_link(self.inputs["3D Mapping"]):
            definitions["mapping.type"] = "localmapping3d"

        return self.create_props(props, definitions, luxcore_name)
