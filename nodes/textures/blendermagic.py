import bpy
from bpy.props import FloatProperty, IntProperty
from ..base import LuxCoreNodeTexture

from ...utils import node as utils_node


class LuxCoreNodeTexBlenderMagic(LuxCoreNodeTexture, bpy.types.Node):
    bl_label = "Blender Magic"
    bl_width_default = 200

    noise_depth: IntProperty(update=utils_node.force_viewport_update, name="Noise Depth", default=2, min=0, soft_max=10, max=25)
    turbulence: FloatProperty(update=utils_node.force_viewport_update, name="Turbulence", default=5, min=0)
    bright: FloatProperty(update=utils_node.force_viewport_update, name="Brightness", default=1.0, min=0)
    contrast: FloatProperty(update=utils_node.force_viewport_update, name="Contrast", default=1.0, min=0)

    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "noise_depth")
        col.prop(self, "turbulence")

        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "blender_magic",
            "noisedepth": self.noise_depth,
            "turbulence": self.turbulence,
            "bright": self.bright,
            "contrast": self.contrast,
        }
        definitions.update(self.inputs["3D Mapping"].export(exporter, depsgraph, props))
        return self.create_props(props, definitions, luxcore_name)
