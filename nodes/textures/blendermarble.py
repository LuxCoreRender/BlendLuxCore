import bpy
from bpy.props import EnumProperty, IntProperty, FloatProperty
from ..base import LuxCoreNodeTexture

from .. import NOISE_BASIS_ITEMS, NOISE_TYPE_ITEMS, MIN_NOISE_SIZE
from ...utils import node as utils_node


class LuxCoreNodeTexBlenderMarble(bpy.types.Node, LuxCoreNodeTexture):
    bl_label = "Blender Marble"
    bl_width_default = 200    

    marble_type_items = [
        ("soft", "Soft", ""),
        ("sharp", "Sharp", ""),
        ("sharper", "Sharper", ""),
    ]

    marble_noise_items = [
        ("sin", "Sin", ""),
        ("saw", "Saw", ""),
        ("tri", "Tri", ""),
    ]

    marble_type: EnumProperty(update=utils_node.force_viewport_update, name="Type", description="Type of noise used", items=marble_type_items, default="soft")
    noise_basis: EnumProperty(update=utils_node.force_viewport_update, name="Noise Basis", description="Basis of noise used", items=NOISE_BASIS_ITEMS,
                                        default="blender_original")
    noise_basis2: EnumProperty(update=utils_node.force_viewport_update, name="Noise Basis 2", description="Second basis of noise used",
                                         items=marble_noise_items, default="sin")
    noise_type: EnumProperty(update=utils_node.force_viewport_update, name="Noise Type", description="Soft or hard noise", items=NOISE_TYPE_ITEMS,
                                       default="soft_noise")
    noise_size: FloatProperty(update=utils_node.force_viewport_update, name="Noise Size", default=0.25, min=MIN_NOISE_SIZE)
    noise_depth: IntProperty(update=utils_node.force_viewport_update, name="Noise Depth", default=2, min=0, soft_max=10, max=25)
    turbulence: FloatProperty(update=utils_node.force_viewport_update, name="Turbulence", default=5.0, min=0)
    bright: FloatProperty(update=utils_node.force_viewport_update, name="Brightness", default=1.0, min=0)
    contrast: FloatProperty(update=utils_node.force_viewport_update, name="Contrast", default=1.0, min=0)

    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "marble_type", expand=True)
        layout.prop(self, "noise_basis2", expand=True)
        layout.prop(self, "noise_type", expand=True)
        layout.prop(self, "noise_basis",)
        column = layout.column(align=True)
        column.prop(self, "noise_size")
        column.prop(self, "noise_depth")
        column.prop(self, "turbulence")

        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def sub_export(self, depsgraph, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "blender_marble",
            "noisebasis": self.noise_basis,
            "noisebasis2": self.noise_basis2,
            "noisedepth": self.noise_depth,
            "noisetype": self.noise_type,
            "noisesize": self.noise_size,
            "turbulence": self.turbulence,
            "bright": self.bright,
            "contrast": self.contrast,
        }
        definitions.update(self.inputs["3D Mapping"].export(exporter, depsgraph, props))
        return self.create_props(props, definitions, luxcore_name)
