from bpy.props import FloatVectorProperty, BoolProperty, EnumProperty, StringProperty
from .. import LuxCoreNodeTexture
from mathutils import Color


class LuxCoreNodeTexConstfloat3(LuxCoreNodeTexture):
    """
    Constant color.
    Note that we do not offer a direct hex code input,
    because that one would have to go through Blender's
    color management.
    """
    bl_label = "Constant Value"

    show_picker = BoolProperty(name="Color Picker", default=True)
    show_values = BoolProperty(name="Values", default=False)

    def update_value(self, context):
        self["value_hsv"] = self.value.hsv

    value = FloatVectorProperty(name="Color", description="A constant color",
                                soft_min=0, soft_max=1, subtype="COLOR",
                                precision=3,
                                update=update_value)

    def update_value_hsv(self, context):
        col = Color()
        col.hsv = self.value_hsv
        self["value"] = col

    # This is a helper property to offer an "HSV view" on the value property
    value_hsv = FloatVectorProperty(soft_min=0, soft_max=1, precision=3,
                                    update=update_value_hsv)

    input_mode_items = [
        ("RGB", "RGB", "", 0),
        ("HSV", "HSV", "", 1),
    ]
    input_mode = EnumProperty(name="Input Mode", items=input_mode_items, default="RGB")

    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        icon = "TRIA_DOWN" if self.show_picker else "TRIA_RIGHT"
        col.prop(self, "show_picker", icon=icon)

        if self.show_picker:
            col.template_color_picker(self, "value", value_slider=True)

        col = layout.column(align=True)
        icon = "TRIA_DOWN" if self.show_values else "TRIA_RIGHT"
        col.prop(self, "show_values", icon=icon)

        if self.show_values:
            row = col.row()
            row.prop(self, "input_mode", expand=True)

            if self.input_mode == "RGB":
                col.prop(self, "value", expand=True, text="")
            elif self.input_mode == "HSV":
                subcol = col.column(align=True)
                subcol.prop(self, "value_hsv", index=0, text="H")
                subcol.prop(self, "value_hsv", index=1, text="S")
                subcol.prop(self, "value_hsv", index=2, text="V")

        layout.prop(self, "value")

    def sub_export(self, exporter, props, luxcore_name=None):
        definitions = {
            "type": "constfloat3",
            "value": list(self.value),
        }

        return self.create_props(props, definitions, luxcore_name)
