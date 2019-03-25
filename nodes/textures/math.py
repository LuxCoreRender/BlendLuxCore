from bpy.props import EnumProperty, FloatProperty, BoolProperty
from .. import LuxCoreNodeTexture
from ... import utils
from ...ui import icons

MIX_DESCRIPTION = (
    "Linear interpolation between two values/textures according to the amount "
    "(0 = use first value, 1 = use second value)"
)

INPUT_SETTINGS = {
    "default": {
        0: ["Value 1", True], # slot index: [name, enabled]
        1: ["Value 2", True],
        2: ["", False]
    },
    "abs": {
        0: ["Value", True],
        1: ["", False],
        2: ["", False]
    },
    "clamp": {
        0: ["Value", True],
        1: ["", False],
        2: ["", False]
    },
    "mix": {
        0: ["Value 1", True],
        1: ["Value 2", True],
        2: ["Fac", True]
    }
}


class LuxCoreNodeTexMath(LuxCoreNodeTexture):
    """Math node with several math operations"""
    bl_label = "Math"

    def change_mode(self, context):
        mode = self.mode if self.mode in INPUT_SETTINGS else "default"
        current_settings = INPUT_SETTINGS[mode]

        for i in current_settings.keys():
            self.inputs[i].name = current_settings[i][0]
            self.inputs[i].enabled = current_settings[i][1]

    mode_items = [
        ("scale", "Multiply", "Value 1 * Value 2", 0),
        ("divide", "Divide", "Value 1 / Value 2", 6),
        ("add", "Add", "Value 1 + Value 2", 1),
        ("subtract", "Subtract", "Value 1 - Value 2", 2),
        ("mix", "Mix", MIX_DESCRIPTION, 3),
        ("clamp", "Clamp", "Clamp the input so it is between min and max values", 4),
        ("abs", "Absolute", "Take the absolute value (remove minus sign)", 5),
        ("power", "Power", "(Value 1) ^ (Value 2)", 7),
        ("lessthan", "Less Than", "Value 1 < Value 2 (returns 0 if false, 1 if true)", 8),
        ("greaterthan", "Greater Than", "Value 1 > Value 2 (returns 0 if false, 1 if true)", 9),
    ]
    mode = EnumProperty(name="Mode", items=mode_items, default="scale", update=change_mode)

    mode_clamp_min = FloatProperty(name="Min", description="", default=0)
    mode_clamp_max = FloatProperty(name="Max", description="", default=1)

    clamp_output = BoolProperty(name="Clamp", default=False,
                                description="Limit the output value to 0..1 range")

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value 1", 1)
        self.add_input("LuxCoreSocketFloatUnbounded", "Value 2", 1)
        self.add_input("LuxCoreSocketFloat0to1", "Fac", 0.5) # for mix mode
        self.inputs["Fac"].enabled = False

        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def draw_label(self):
        # Use the name of the selected operation as displayed node name
        for elem in self.mode_items:
            if self.mode in elem:
                return elem[1]

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text="")

        if self.mode != "clamp":
            layout.prop(self, "clamp_output")

        if self.mode == "clamp":
            layout.prop(self, "mode_clamp_min")
            layout.prop(self, "mode_clamp_max")

            if self.mode_clamp_min > self.mode_clamp_max:
                layout.label("Min should be smaller than max!", icon=icons.WARNING)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": self.mode,
        }

        if self.mode == "abs":
            definitions["texture"] = self.inputs[0].export(exporter, props)
        elif self.mode == "clamp":
            definitions["texture"] = self.inputs[0].export(exporter, props)
            definitions["min"] = self.mode_clamp_min
            definitions["max"] = self.mode_clamp_max
        elif self.mode == "mix":
            definitions["texture1"] = self.inputs[0].export(exporter, props)
            definitions["texture2"] = self.inputs[1].export(exporter, props)
            definitions["amount"] = self.inputs[2].export(exporter, props)
        elif self.mode == "power":
            definitions["base"] = self.inputs[0].export(exporter, props)
            definitions["exponent"] = self.inputs[1].export(exporter, props)
        else:
            definitions["texture1"] = self.inputs[0].export(exporter, props)
            definitions["texture2"] = self.inputs[1].export(exporter, props)

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
