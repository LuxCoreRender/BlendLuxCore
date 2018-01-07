import bpy
from bpy.props import EnumProperty, FloatProperty, IntProperty
from .. import LuxCoreNodeTexture

from .. import NOISE_BASIS_ITEMS
from .. import NOISE_TYPE_ITEMS

from .. import sockets
from ... import utils

class LuxCoreNodeTexBlenderStucci(LuxCoreNodeTexture):
    bl_label = "Blender Stucci"
    bl_width_min = 200    

    stucci_type_items = [
        ("plastic", "Plastic", ""),
        ("wall_in", "Wall In", ""),
        ("wall_out", "Wall Out", ""),
    ]

    stuccitype = EnumProperty(name="Type", description="Type of noise used", items=stucci_type_items, default="plastic")
    noisebasis = EnumProperty(name="Basis", description="Basis of noise used", items=NOISE_BASIS_ITEMS,
                                        default="blender_original")
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
        layout.prop(self, "stuccitype", expand=True)
        layout.prop(self, "noisebasis")
        layout.prop(self, "noisetype", expand=True)
        layout.prop(self, "noisesize")
        layout.prop(self, "turbulence")
        layout.separator()
        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def export(self, props, luxcore_name=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(props)
       
        definitions = {
            "type": "blender_stucci",
            "stuccitype": self.stuccitype,
            "noisebasis": self.noisebasis,
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
