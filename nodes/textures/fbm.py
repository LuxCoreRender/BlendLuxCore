import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexfBM(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "fBM"
    bl_width_default = 200


    octaves: IntProperty(update=utils_node.force_viewport_update, name="Octaves", default=8, min=1, max=29)
    roughness: FloatProperty(update=utils_node.force_viewport_update, name="Roughness", default=0.5, min=0, max=1)
    
    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "octaves")
        layout.prop(self, "roughness")
    
    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "fbm",
            "octaves": self.octaves,
            "roughness": self.roughness,
        }
        definitions.update(self.inputs["3D Mapping"].export(exporter, depsgraph, props))
        return self.create_props(props, definitions, luxcore_name)
