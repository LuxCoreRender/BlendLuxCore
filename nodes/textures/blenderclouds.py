import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty
from .. import LuxCoreNodeTexture

from .. import NOISE_BASIS_ITEMS
from .. import NOISE_TYPE_ITEMS

from .. import sockets
from ... import utils

class LuxCoreNodeTexBlenderClouds(LuxCoreNodeTexture):
    bl_label = "Blender Clouds"
    bl_width_default = 200

    noise_type = EnumProperty(name="Noise Type", description="Soft or hard noise", items=NOISE_TYPE_ITEMS,
                                       default="soft_noise")
    noise_basis = EnumProperty(name="Basis", description="Basis of noise used", items=NOISE_BASIS_ITEMS,
                                        default="blender_original")
    noise_size = FloatProperty(name="Noise Size", default=0.25, min=0)
    noise_depth = IntProperty(name="Noise Depth", default=2, min=0)
    bright = FloatProperty(name="Brightness", default=1.0, min=0)
    contrast = FloatProperty(name="Contrast", default=1.0, min=0)

    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "noise_type", expand=True)
        layout.prop(self, "noise_basis")
        layout.prop(self, "noise_size")
        layout.prop(self, "noise_depth")
        layout.separator()
        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def export(self, props, luxcore_name=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(props)
       
        definitions = {
            "type": "blender_clouds",
            "noisetype": self.noise_type,
            "noisebasis": self.noise_basis,
            "noisesize": self.noise_size,
            "noisedepth": self.noise_depth,
            "bright": self.bright,
            "contrast": self.contrast,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation),
        }
        
        return self.base_export(props, definitions, luxcore_name)
