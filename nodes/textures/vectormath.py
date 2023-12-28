import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from ..base import LuxCoreNodeTexture
from ...ui import icons
from .math import MIX_DESCRIPTION
from ...utils import node as utils_node


class LuxCoreNodeTexVectorMath(LuxCoreNodeTexture, bpy.types.Node):
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
            id = self.inputs.find["Vector 2"]
            self.inputs[id].enabled = False
        else:
            self.inputs[1].name = "Vector 1"
            id = self.inputs.find["Vector 2"]
            self.inputs[id].enabled = True
        
        if self.mode == "mix":
            id = self.inputs.find["Fac"]
            self.inputs[id].enabled = True
        else:
            id = self.inputs.find["Fac"]
            self.inputs[id].enabled = False

        utils_node.force_viewport_update(self, context)

    mode: EnumProperty(name="Mode", items=mode_items, default="scale", update=change_mode)

    mode_clamp_min: FloatProperty(update=utils_node.force_viewport_update, name="Min", description="", default=0)
    mode_clamp_max: FloatProperty(update=utils_node.force_viewport_update, name="Max", description="", default=1)

    def draw_label(self):
        # Use the name of the selected operation as displayed node name
        for elem in self.mode_items:
            if self.mode in elem:
                return elem[1]

    def init(self, context):
        self.add_input("LuxCoreSocketFloat0to1", "Fac", 1)
        self.inputs["Fac"].hide = True
        self.add_input("LuxCoreSocketVector", "Vector 1", (0, 0, 0))
        self.add_input("LuxCoreSocketVector", "Vector 2", (0, 0, 0))

        self.outputs.new("LuxCoreSocketVector", "Vector")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")

        if self.mode == "clamp":
            layout.prop(self, "mode_clamp_min")
            layout.prop(self, "mode_clamp_max")

            if self.mode_clamp_min > self.mode_clamp_max:
                layout.label(text="Min should be smaller than max!", icon=icons.WARNING)

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": self.mode,
        }
        
        if self.mode == "abs":
            definitions["texture"] = self.inputs["Vector"].export(exporter, depsgraph, props)
        elif self.mode == "clamp":
            definitions["texture"] = self.inputs["Vector"].export(exporter, depsgraph, props)
            definitions["min"] = self.mode_clamp_min
            definitions["max"] = self.mode_clamp_max
        else:
            definitions["texture1"] = self.inputs["Vector 1"].export(exporter, depsgraph, props)
            definitions["texture2"] = self.inputs["Vector 2"].export(exporter, depsgraph, props)

            if self.mode == "mix":
                definitions["amount"] = self.inputs["Fac"].export(exporter, depsgraph, props)

        return self.create_props(props, definitions, luxcore_name)
