import bpy
from bpy.props import FloatProperty
from .. import LuxCoreNodeTexture
from ... import utils
from .. import COLORDEPTH_DESC

class LuxCoreNodeTexColorAtDepth(LuxCoreNodeTexture):
    bl_label = "Color at depth"
    bl_width_default = 200
    
    color_depth = FloatProperty(name="Absorption Depth", default=1.0, min=0,
                                subtype="DISTANCE", unit="LENGTH",
                                description=COLORDEPTH_DESC)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Absorption", (1, 1, 1))
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "color_depth")
    
    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        abs_col = self.inputs["Absorption"].export(exporter, props)

        definitions = {
            "type": "colordepth",
            "kt": abs_col,
            "depth": self.color_depth,
        }
        
        return self.create_props(props, definitions, luxcore_name)
