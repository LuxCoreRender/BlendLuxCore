import bpy
from ..base import LuxCoreNodeTexture


DATAINDEX_RANDOM_PER_ISLAND = 0


class LuxCoreNodeTexRandomPerIsland(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Random Per Island"
    bl_width_default = 130

    def init(self, context):
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "hitpointtriangleaov",
            "dataindex": DATAINDEX_RANDOM_PER_ISLAND,
        }

        return self.create_props(props, definitions, luxcore_name)
