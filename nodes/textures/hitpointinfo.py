from bpy.props import EnumProperty
from .. import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexHitpointInfo(LuxCoreNodeTexture):
    """ Access to various hitpoint attributes """
    bl_label = "Hitpoint Info"
    bl_width_default = 150

    def init(self, context):
        self.outputs.new("LuxCoreSocketVector", "Shading Normal")
        self.outputs.new("LuxCoreSocketVector", "Position")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {}
        if output_socket == self.outputs["Shading Normal"]:
            definitions["type"] = "shadingnormal"
        elif output_socket == self.outputs["Position"]:
            definitions["type"] = "position"
        else:
            raise Exception("Unknown output socket:", output_socket)
        return self.create_props(props, definitions, luxcore_name)
