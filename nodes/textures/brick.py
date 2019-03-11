import bpy
from bpy.props import EnumProperty, FloatProperty
from .. import LuxCoreNodeTexture
from ... import utils


class LuxCoreNodeTexBrick(LuxCoreNodeTexture):
    bl_label = "Brick"
    bl_width_default = 200   

    bond_type_items = [
        ("running", "Running", ""),
        ("flemish", "Flemish", ""),
        ("english", "English", ""),
        ("herringbone", "Herringbone", ""),
        ("basket", "Basket", ""),
        ("chain link", "Chain link", ""),
    ]
    
    brickbond = EnumProperty(name="Bond type", description="Type of brick bond used", items=bond_type_items, default="running")
    brickwidth = FloatProperty(name="Brick Width", description="Width of bricks", min=0, subtype="DISTANCE", unit="LENGTH", default=0.3)
    brickheight = FloatProperty(name="Brick Height", description="Height of bricks", min=0, subtype="DISTANCE", unit="LENGTH", default=0.1)
    brickdepth = FloatProperty(name="Brick Depth", description="Depth of bricks", min=0, subtype="DISTANCE", unit="LENGTH", default=0.15)
    mortarsize = FloatProperty(name="Mortar Size", description="Size of mortar", min=0, subtype="DISTANCE", unit="LENGTH", default=0.01)
    brickrun = FloatProperty(name="Brick Run", description="Run of bricks", min=0, subtype="DISTANCE", unit="LENGTH", default=0.75)
    brickbevel = FloatProperty(name="Brick Bevel", description="Bevel strengh of bricks", min=0, subtype="DISTANCE", unit="LENGTH", default=0.0)
    
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
    
    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):        
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, props)

        definitions = {
            "type": "brick",
            "brickbond": self.brickbond,            
            "bricktex": self.inputs["bricktex"].export(exporter, props),
            "mortartex": self.inputs["mortartex"].export(exporter, props),
            "brickmodtex": self.inputs["brickmodtex"].export(exporter, props),
            "brickwidth": self.brickwidth,
            "brickheight": self.brickheight,
            "brickdepth": self.brickdepth,
            "mortarsize": self.mortarsize,
            "brickrun": self.brickrun,
            "brickbevel": self.brickbevel,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }       
        
        return self.create_props(props, definitions, luxcore_name)
