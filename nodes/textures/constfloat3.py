from bpy.props import FloatVectorProperty, BoolProperty
from .. import LuxCoreNodeTexture


class LuxCoreNodeTexConstfloat3(LuxCoreNodeTexture):
    """ Constant color """
    bl_label = "Constant Value"

    picker = BoolProperty(name="Color Picker", default=True)
    value = FloatVectorProperty(name="Color", description="A constant color",
                                soft_min=0, soft_max=1, subtype="COLOR")

    def init(self, context):
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        icon = "TRIA_DOWN" if self.picker else "TRIA_RIGHT"
        col.prop(self, "picker", icon=icon)

        if self.picker:
            col.template_color_picker(self, "value", value_slider=True)

        layout.prop(self, "value")

    def export(self, exporter, props, luxcore_name=None):
        definitions = {
            "type": "constfloat3",
            "value": list(self.value),
        }

        return self.base_export(props, definitions, luxcore_name)
