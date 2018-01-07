import bpy
from bpy.props import EnumProperty, IntProperty, FloatProperty
from .. import LuxCoreNodeTexture

from .. import NOISE_BASIS_ITEMS
from .. import NOISE_TYPE_ITEMS

from .. import sockets
from ... import utils

class LuxCoreNodeTexBlenderMarble(LuxCoreNodeTexture):
    bl_label = "Blender Marble"
    bl_width_min = 200    

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

    marbletype = EnumProperty(name="Type", description="Type of noise used", items=marble_type_items, default="soft")
    noisebasis = EnumProperty(name="Noise Basis", description="Basis of noise used", items=NOISE_BASIS_ITEMS,
                                        default="blender_original")
    noisebasis2 = EnumProperty(name="Noise Basis 2", description="Second basis of noise used",
                                         items=marble_noise_items, default="sin")
    noisetype = EnumProperty(name="Noise Type", description="Soft or hard noise", items=NOISE_TYPE_ITEMS,
                                       default="soft_noise")
    noisesize = FloatProperty(name="Noise Size", default=0.25, min=0)
    noisedepth = IntProperty(name="Noise Depth", default=2, min=0)
    turbulence = FloatProperty(name="Turbulence", default=5.0)
    bright = FloatProperty(name="Brightness", default=1.0, min=0)
    contrast = FloatProperty(name="Contrast", default=1.0, min=0)

    
    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "marbletype", expand=True)
        layout.prop(self, "noisebasis2", expand=True)
        layout.prop(self, "noisetype", expand=True)
        layout.prop(self, "noisebasis",)
        column = layout.column(align=True)
        column.prop(self, "noisesize")
        column.prop(self, "noisedepth")
        layout.prop(self, "turbulence")
        layout.separator()
        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def export(self, props, luxcore_name=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(props)
       
        definitions = {
            "type": "blender_marble",
            "noisebasis": self.noisebasis,
            "noisebasis2": self.noisebasis2,
            "noisetype": self.noisetype,
            "noisesize": self.noisesize,
            "turbulence": self.turbulence,
            "bright": self.bright,
            "contrast": self.contrast,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation),
        }
        
        return self.base_export(props, definitions, luxcore_name)
