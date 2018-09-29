import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from .. import LuxCoreNodeTexture
from ... import utils


class LuxCoreNodeTexColorMix(LuxCoreNodeTexture):
    bl_label = "ColorMix"
    bl_width_default = 200

    mode_items = [
        ("scale", "Multiply", ""),
        ("add", "Add", ""),
        ("subtract", "Subtract", ""),
        ("mix", "Mix", "Mix between two values/textures according to the amount (0 = use first value, 1 = use second value"),
        ("clamp", "Clamp", "Clamp the input so it is between min and max values"),
        ("abs", "Absolute", "Take the absolute value (remove minus sign)"),
    ]

    def change_mode(self, context):
        if self.mode in {"scale", "add", "subtract", "mix"}:
            self.inputs[1].name = "Color 1"
            self.inputs["Color 2"].enabled = True
        else:
            self.inputs[1].name = "Color"
            self.inputs["Color 2"].enabled = False
        
        if self.mode == "mix":
            self.inputs["Fac"].enabled = True
        else:
            self.inputs["Fac"].enabled = False

    mode = EnumProperty(name="Mode", items=mode_items, default="mix", update=change_mode)
    clamp_output = BoolProperty(name="Clamp", default=False, description="Limit the output value to 0..1 range")

    mode_clamp_min = FloatProperty(name="Min", description="", default=0)
    mode_clamp_max = FloatProperty(name="Max", description="", default=1)

    def draw_label(self):
        # Use the name of the selected operation as displayed node name
        for elem in self.mode_items:
            if self.mode in elem:
                return elem[1]

    def init(self, context):
        self.add_input("LuxCoreSocketFloat0to1", "Fac", 1)
        self.add_input("LuxCoreSocketColor", "Color 1", (0.7, 0.7, 0.7))
        self.add_input("LuxCoreSocketColor", "Color 2", (0.04, 0.04, 0.04))

        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")

        if self.mode != "clamp":
            layout.prop(self, "clamp_output")

        if self.mode == "clamp":
            layout.prop(self, "mode_clamp_min")
            layout.prop(self, "mode_clamp_max")

            if self.mode_clamp_min > self.mode_clamp_max:
                layout.label("Min should be smaller than max!", icon="ERROR")

    def sub_export(self, exporter, props, luxcore_name=None):
        definitions = {
            "type": self.mode,
        }
        
        if self.mode == "abs":
            definitions["texture"] = self.inputs["Color"].export(exporter, props)
        elif self.mode == "clamp":
            definitions["texture"] = self.inputs["Color"].export(exporter, props)
            definitions["min"] = self.mode_clamp_min
            definitions["max"] = self.mode_clamp_max
        else:
            definitions["texture1"] = self.inputs["Color 1"].export(exporter, props)
            definitions["texture2"] = self.inputs["Color 2"].export(exporter, props)

            if self.mode == "mix":
                definitions["amount"] = self.inputs["Fac"].export(exporter, props)

        luxcore_name = self.create_props(props, definitions, luxcore_name)

        if self.clamp_output and self.mode != "clamp":
            # Implicitly create a clamp texture with unique name
            tex_name = luxcore_name + "_clamp"
            helper_prefix = "scene.textures." + tex_name + "."
            helper_defs = {
                "type": "clamp",
                "texture": luxcore_name,
                "min": 0,
                "max": 1,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

            # The helper texture gets linked in front of this node
            return tex_name
        else:
            return luxcore_name
