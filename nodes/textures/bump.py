import bpy
from bpy.props import FloatProperty
from ..base import LuxCoreNodeTexture
from ..sockets import LuxCoreSocketFloat
from ... import utils
from ...utils import node as utils_node


class LuxCoreSocketBumpHeight(bpy.types.NodeSocket, LuxCoreSocketFloat):
    # Allow negative values for inverting the bump. These values are in meters.
    default_value: FloatProperty(default=0.001, soft_min=-0.01, soft_max=0.01,
                                  precision=3, step=0.001,
                                  subtype="DISTANCE", description="Bump height",
                                  update=utils_node.force_viewport_update)


class LuxCoreNodeTexBump(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Bump"
    bl_width_default = 180

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value", 0.0)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height", 0.001)

        self.outputs.new("LuxCoreSocketBump", "Bump")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "scale",
            "texture1": self.inputs["Value"].export(exporter, depsgraph, props),
            "texture2": self.inputs["Bump Height"].export(exporter, depsgraph, props),
        }
        return self.create_props(props, definitions, luxcore_name)
