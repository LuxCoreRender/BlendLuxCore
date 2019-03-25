from bpy.props import BoolProperty, EnumProperty, FloatProperty
from .. import LuxCoreNodeTexture
from ...ui import icons
from .math import MIX_DESCRIPTION


class LuxCoreNodeTexVectorMath(LuxCoreNodeTexture):
    bl_label = "Vector Math"
    bl_width_default = 200

    mode_items = [
        ("scale", "Multiply", ""),
        ("add", "Add", ""),
        ("subtract", "Subtract", ""),
        ("mix", "Mix", MIX_DESCRIPTION),
        ("clamp", "Clamp", "Clamp the input so it is between min and max values"),
        ("abs", "Absolute", "Take the absolute value (remove minus sign)"),
    ]

    def change_mode(self, context):
        if self.mode in {"clamp", "abs"}:
            self.inputs[1].name = "Vector"
            self.inputs["Vector 2"].enabled = False
        else:
            self.inputs[1].name = "Vector 1"
            self.inputs["Vector 2"].enabled = True
        
        if self.mode == "mix":
            self.inputs["Fac"].enabled = True
        else:
            self.inputs["Fac"].enabled = False

    mode = EnumProperty(name="Mode", items=mode_items, default="scale", update=change_mode)

    mode_clamp_min = FloatProperty(name="Min", description="", default=0)
    mode_clamp_max = FloatProperty(name="Max", description="", default=1)

    def draw_label(self):
        # Use the name of the selected operation as displayed node name
        for elem in self.mode_items:
            if self.mode in elem:
                return elem[1]

    def init(self, context):
        self.add_input("LuxCoreSocketFloat0to1", "Fac", 1)
        self.inputs["Fac"].enabled = False
        self.add_input("LuxCoreSocketVector", "Vector 1", (0, 0, 0))
        self.add_input("LuxCoreSocketVector", "Vector 2", (0, 0, 0))

        self.outputs.new("LuxCoreSocketVector", "Vector")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")

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
            definitions["texture"] = self.inputs["Vector"].export(exporter, props)
        elif self.mode == "clamp":
            definitions["texture"] = self.inputs["Vector"].export(exporter, props)
            definitions["min"] = self.mode_clamp_min
            definitions["max"] = self.mode_clamp_max
        else:
            definitions["texture1"] = self.inputs["Vector 1"].export(exporter, props)
            definitions["texture2"] = self.inputs["Vector 2"].export(exporter, props)

            if self.mode == "mix":
                definitions["amount"] = self.inputs["Fac"].export(exporter, props)

        return self.create_props(props, definitions, luxcore_name)
