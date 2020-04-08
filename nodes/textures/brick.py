import bpy
from bpy.props import EnumProperty, FloatProperty
from ..base import LuxCoreNodeTexture
from ... import utils
from ...utils import node as utils_node


class LuxCoreNodeTexBrick(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Brick"
    bl_width_default = 200   

    bond_type_items = [
        ("running", "Running", "", 0),
        ("flemish", "Flemish", "", 1),
        ("english", "English", "", 2),
        ("herringbone", "Herringbone", "", 3),
        ("basket", "Basket", "", 4),
        ("chain_link", "Chain link", "", 5),
    ]
    
    brickbond: EnumProperty(update=utils_node.force_viewport_update, name="Bond type", description="Type of brick bond used", items=bond_type_items, default="running")
    brickwidth: FloatProperty(update=utils_node.force_viewport_update, name="Brick Width", description="Width of bricks", min=0, subtype="DISTANCE", unit="LENGTH", default=0.3)
    brickheight: FloatProperty(update=utils_node.force_viewport_update, name="Brick Height", description="Height of bricks", min=0, subtype="DISTANCE", unit="LENGTH", default=0.1)
    brickdepth: FloatProperty(update=utils_node.force_viewport_update, name="Brick Depth", description="Depth of bricks", min=0, subtype="DISTANCE", unit="LENGTH", default=0.15)
    mortarsize: FloatProperty(update=utils_node.force_viewport_update, name="Mortar Size", description="Size of mortar", min=0, subtype="DISTANCE", unit="LENGTH", default=0.01)
    brickrun: FloatProperty(update=utils_node.force_viewport_update, name="Brick Run", description="Run of bricks", min=0, subtype="PERCENTAGE", precision=1, default=75)
    brickbevel: FloatProperty(update=utils_node.force_viewport_update, name="Brick Bevel", description="Bevel strength of bricks", min=0, subtype="DISTANCE", unit="LENGTH", default=0.0)
    
    def init(self, context):
        self.add_input("LuxCoreSocketColor", "bricktex", (0.7, 0.7, 0.7))
        self.add_input("LuxCoreSocketColor", "mortartex", (0.2, 0.2, 0.2))
        self.add_input("LuxCoreSocketColor", "brickmodtex", (1.0, 1.0, 1.0))
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "brickbond")
        layout.prop(self, "brickwidth")
        layout.prop(self, "brickheight")
        layout.prop(self, "brickdepth")
        layout.prop(self, "mortarsize")
        layout.prop(self, "brickrun")
        layout.prop(self, "brickbevel")
    
    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        mapping_type, uvindex, transformation = self.inputs["3D Mapping"].export(exporter, depsgraph, props)

        definitions = {
            "type": "brick",
            "brickbond": self.brickbond,            
            "bricktex": self.inputs["bricktex"].export(exporter, depsgraph, props),
            "mortartex": self.inputs["mortartex"].export(exporter, depsgraph, props),
            "brickmodtex": self.inputs["brickmodtex"].export(exporter, depsgraph, props),
            "brickwidth": self.brickwidth,
            "brickheight": self.brickheight,
            "brickdepth": self.brickdepth,
            "mortarsize": self.mortarsize,
            "brickrun": self.brickrun/100.0,
            "brickbevel": self.brickbevel,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation),
        }       

        if mapping_type == "uvmapping3d":
            definitions["mapping.uvindex"] = uvindex

        return self.create_props(props, definitions, luxcore_name)
