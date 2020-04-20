import bpy
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node
from ...ui import icons


class LuxCoreNodeTexBump(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Bump"
    bl_width_default = 190

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value", 0.0)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height", 0.001)

        self.outputs.new("LuxCoreSocketBump", "Bump")

    def draw_buttons(self, context, layout):
        utils_node.draw_uv_info(context, layout)

        show_triplanar_warning = False
        value_node = utils_node.get_linked_node(self.inputs["Value"])
        if value_node and value_node.bl_idname == "LuxCoreNodeTexTriplanar":
            show_triplanar_warning = True
        else:
            height_node = utils_node.get_linked_node(self.inputs["Bump Height"])
            if height_node and height_node.bl_idname == "LuxCoreNodeTexTriplanar":
                show_triplanar_warning = True

        if show_triplanar_warning:
            layout.label(text="Use triplanar bump node instead!", icon=icons.WARNING)

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "scale",
            "texture1": self.inputs["Value"].export(exporter, depsgraph, props),
            "texture2": self.inputs["Bump Height"].export(exporter, depsgraph, props),
        }
        return self.create_props(props, definitions, luxcore_name)
