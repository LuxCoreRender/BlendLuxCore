from bpy.props import EnumProperty, FloatProperty
from .. import LuxCoreNodeTexture

from .. import NOISE_BASIS_ITEMS

from ... import utils


class LuxCoreNodeTexBlenderDistortedNoise(LuxCoreNodeTexture):
    bl_label = "Blender Distorted Noise"
    bl_width_default = 200

    noise_basis = EnumProperty(name="Noise Basis", description="Type of noise used", items=NOISE_BASIS_ITEMS,
                                        default="blender_original")
    noise_type = EnumProperty(name="Type", description="Type of noise used", items=NOISE_BASIS_ITEMS,
                                  default="blender_original")
    dist_amount = FloatProperty(name="Distortion", default=1.00)
    noise_size = FloatProperty(name="Noise Size", default=0.25, min=0)    
    bright = FloatProperty(name="Brightness", default=1.0, min=0)
    contrast = FloatProperty(name="Contrast", default=1.0, min=0)

    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "noise_basis")
        layout.prop(self, "noise_type")

        col = layout.column(align=True)
        col.prop(self, "noise_size")
        col.prop(self, "dist_amount")

        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, props)
       
        definitions = {
            "type": "blender_distortednoise",
            "noise_distortion": self.noise_type,
            "noisebasis": self.noise_basis,            
            "noisesize": self.noise_size,
            "distortion": self.dist_amount,
            "bright": self.bright,
            "contrast": self.contrast,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }
        
        return self.create_props(props, definitions, luxcore_name)
