import bpy
from ..base import LuxCoreNodeTexture
from ...utils import node as utils_node


DATAINDEX_RANDOM_PER_ISLAND = 0


class LuxCoreNodeTexRandomPerIsland(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Random Per Island"
    bl_width_default = 130

    def init(self, context):
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")
        # This node potentially requires a mesh re-export in viewport, 
        # because it depends on a LuxCore shape to pre-process the data
        utils_node.force_viewport_mesh_update2(self.id_data)
        

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "hitpointtriangleaov",
            "dataindex": DATAINDEX_RANDOM_PER_ISLAND,
        }

        return self.create_props(props, definitions, luxcore_name)
