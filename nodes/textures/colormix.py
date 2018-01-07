import bpy
from bpy.props import BoolProperty, EnumProperty
from .. import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexColorMix(LuxCoreNodeTexture):
    bl_label = "ColorMix"
    bl_width_min = 200

    mode_items = [
        ("scale", "Multiply", ""),
        ("add", "Add", ""),
        ("subtract", "Subtract", ""),
        ("mix", "Mix", "Mix between two values/textures according to the amount (0 = use first value, 1 = use second value"),
        ("clamp", "Clamp", "Clamp the input so it is between min and max values"),
        ("abs", "Absolute", "Take the absolute value (remove minus sign)"),
    ]

    def change_mode(self, context):
        self.inputs["Min"].enabled = (self.mode == "clamp")
        self.inputs["Max"].enabled = (self.mode == "clamp")

    mode = EnumProperty(name="Mode", items=mode_items, default="mix", update=change_mode)
    clamp_output = BoolProperty(name="Clamp", default=False, description="Limit the output value to 0..1 range")

    def init(self, context):
        self.add_input("LuxCoreSocketFloat0to1", "Fac", 1)
        self.add_input("LuxCoreSocketFloat", "Min", 0.0)
        self.add_input("LuxCoreSocketFloat", "Max", 1.0)

        self.add_input("LuxCoreSocketColor", "Color 1", (0.7, 0.7, 0.7))
        self.add_input("LuxCoreSocketColor", "Color 2", (0.04, 0.04, 0.04))

        self.outputs.new("LuxCoreSocketColor", "Color")

        self.inputs["Min"].enabled = False
        self.inputs["Max"].enabled = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")
        layout.prop(self, "clamp_output")

    def export(self, props, luxcore_name=None):
        if self.mode == "mix":            
            definitions = {
                "type": "mix",
                "amount": self.inputs["Fac"].export(props),
                "texture1": self.inputs["Color 1"].export(props),
                "texture2": self.inputs["Color 2"].export(props),
        }
        
        return self.base_export(props, definitions, luxcore_name)
