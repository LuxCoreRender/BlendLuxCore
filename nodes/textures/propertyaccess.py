import bpy
from bpy.props import StringProperty, PointerProperty
from .. import LuxCoreNodeTexture


class LuxCoreNodeTexPropertyAccess(LuxCoreNodeTexture):
    bl_label = "PropertyAccess"

    datablock = PointerProperty(name="Datablock", type=bpy.types.Object)
    prop = StringProperty(name="Prop")

    def init(self, context):
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def draw_label(self):
        if self.datablock and self.prop:
            return self.datablock.name + "." + self.prop
        else:
            return self.bl_label

    def draw_buttons(self, context, layout):
        layout.prop(self, "datablock")
        layout.prop(self, "prop")

    def sub_export(self, exporter, props, luxcore_name=None):
        if self.datablock and self.prop:
            value = getattr(self.datablock, self.prop, 0)

            try:
                value = list(value)
            except TypeError:
                # Not iterable
                value = [value, value, value]
        else:
            value = [0, 0, 0]

        definitions = {
            "type": "constfloat3",
            "value": value,
        }

        return self.create_props(props, definitions, luxcore_name)
