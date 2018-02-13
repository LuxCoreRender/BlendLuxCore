"""A BlendLuxCore node to provide index of refraction preset values for
    LuxCoreRender in Blender"""
# <pep8 compliant>
import bpy
from bpy.props import FloatProperty, StringProperty
from .. import LuxCoreNodeTexture
from ...operators import ior_presets


class LuxCoreNodeIORPreset(LuxCoreNodeTexture):
    """ Index of Refraction Preset node """
    bl_label = "IOR Preset"
    bl_width_min = 180
    bl_width_default = 180

    ior_name_text = StringProperty(name="IOR Name", description="The name of"
                                   " the selected Index of Refraction preset")
    ior_value_text = StringProperty(name="IOR Value", description="The value "
                                    "of the selected Index of Refraction"
                                    " preset")

    def get_node_data_path(self):
        return bpy.data.node_groups[self.id_data.name].nodes[self.name]

    def update_ior_value_float(self, context):
        self.get_node_data_path().outputs[0].default_value = \
            self.ior_value_float
        # Change the node label to indicate the selected IOR preset
        self.label = "IOR: {} ({})".format(self.ior_name_text,
                                           self.ior_value_text)
        return None

    ior_value_float = FloatProperty(name="IOR Float",
                                    update=update_ior_value_float)

    def init(self, context):
        self.label = "IOR Preset"
        self.outputs.new("LuxCoreSocketIOR", "IOR")
        if not (self.ior_name_text and self.ior_value_text):
            item = ior_presets.LuxCoreIORPresetValues.get_item()
            data_path = bpy.data.node_groups[self.id_data.name].\
                nodes[self.name]
            data_path.ior_name_text = item[0]
            data_path.ior_value_text = str(item[1])
            data_path.ior_value_float = item[1]

    def draw_buttons(self, context, layout):
        layout.alignment = "LEFT"

        # Alpha-sorting operator
        row1 = layout.row(align=True)
        row1.scale_x = 1.2
        row1.prop(self, "ior_name_text", text="", emboss=False)
        op_alpha = row1.operator("luxcore.ior_preset_names", icon="SORTALPHA")

        # Numeric-sorting operator
        row2 = layout.row(align=False)
        row2.scale_x = 1.2
        row2.prop(self, "ior_value_text", text="Value", emboss=False)
        op_num = row2.operator("luxcore.ior_preset_values", icon="SORTSIZE")

        for operator in [op_alpha, op_num]:
            operator.node_name = self.name
            operator.node_tree_name = self.id_data.name

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "constfloat1",
            "value": self.ior_value_float,
        }
        return self.base_export(props, definitions, luxcore_name)
