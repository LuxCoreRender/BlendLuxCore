import bpy
from bpy.props import StringProperty, PointerProperty
from .. import LuxCoreNodeTexture
from ...utils import ui as utils_ui


class LuxCoreNodeTexPropertyAccess(LuxCoreNodeTexture):
    bl_label = "PropertyAccess"

    datablock = PointerProperty(name="Datablock", type=bpy.types.Object)
    attribute_path = StringProperty(name="Attribute")
    error = StringProperty(name="Error")

    def init(self, context):
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def draw_label(self):
        if self.datablock and self.attribute_path:
            return self.datablock.name + "." + self.attribute_path
        else:
            return self.bl_label

    def draw_buttons(self, context, layout):
        layout.prop(self, "datablock")
        layout.prop(self, "attribute_path")
        if self.error:
            row = layout.row()
            row.label("", icon="CANCEL")
            row.prop(self, "error")

    def sub_export(self, exporter, props, luxcore_name=None):
        self.error = ""
        utils_ui.tag_region_for_redraw(bpy.context, "NODE_EDITOR", "WINDOW")

        try:
            if self.datablock and self.attribute_path:
                value = self.datablock
                for attrib in self.attribute_path.split("."):
                    value = getattr(value, attrib)

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
        except Exception as error:
            import traceback
            traceback.print_exc()

            self.error = str(error)
            utils_ui.tag_region_for_redraw(bpy.context, "NODE_EDITOR", "WINDOW")

            definitions = {
                "type": "constfloat1",
                "value": 0,
            }

            return self.create_props(props, definitions, luxcore_name)

