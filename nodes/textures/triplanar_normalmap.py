import bpy
from bpy.props import BoolProperty, FloatProperty
from ..base import LuxCoreNodeTexture
from ... import utils
from ...utils import node as utils_node
from .imagemap import NORMAL_SCALE_DESC


class LuxCoreNodeTexTriplanarNormalmap(LuxCoreNodeTexture, bpy.types.Node):
    bl_label = "Triplanar Normal Mapping"
    bl_width_default = 165

    def update_multiple_textures(self, context):
        if self.multiple_textures:
            id = self.inputs.find("Color")
            self.inputs[id].name = "Color X"
        else:
            id = self.inputs.find("Color X")
            self.inputs[id].name = "Color"

        self.inputs[id].name = "Color Y"
        self.inputs[id].enabled = self.multiple_textures
        self.inputs[id].name = "Color Y"
        self.inputs[id].enabled = self.multiple_textures
        
        utils_node.force_viewport_update(self, context)

    multiple_textures: BoolProperty(update=update_multiple_textures, name="Multiple Textures", default=False,
                                    description="Makes it possible to assign textures to each axis individually")
    
    scale: FloatProperty(update=utils_node.force_viewport_update, name="Height", default=1, min=0, soft_max=5,
                         description=NORMAL_SCALE_DESC)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", [0.5, 0.5, 1])
        self.add_input("LuxCoreSocketColor", "Color Y", [0.5, 0.5, 1])
        self.inputs["Color Y"].enabled = False
        self.add_input("LuxCoreSocketColor", "Color Z", [0.5, 0.5, 1])
        self.inputs["Color Z"].enabled = False
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketBump", "Bump")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multiple_textures")
        layout.prop(self, "scale")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        if self.multiple_textures:
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
        }
        definitions.update(self.inputs["3D Mapping"].export(exporter, depsgraph, props))

        if not utils_node.get_link(self.inputs["3D Mapping"]):
            definitions["mapping.type"] = "localmapping3d"

        luxcore_name = self.create_props(props, definitions, luxcore_name)
        
        tex_name = luxcore_name + "_normalmap"
        helper_prefix = "scene.textures." + tex_name + "."
        helper_defs = {
            "type": "normalmap",
            "texture": luxcore_name,
            "scale": self.scale,
        }
        props.Set(utils.create_props(helper_prefix, helper_defs))

        # The helper texture gets linked in front of this node
        return tex_name
