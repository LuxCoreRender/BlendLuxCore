import bpy
from bpy.props import EnumProperty
from .. import LuxCoreNodeTexture

from .. import NOISE_BASIS_ITEMS
from .. import NOISE_TYPE_ITEMS

from .. import sockets
from ... import utils

class LuxCoreNodeTexBlenderWood(LuxCoreNodeTexture):
    bl_label = "Blender Wood"
    bl_width_min = 200    

    wood_type_items = [
        ("bands", "Bands", ""),
        ("rings", "Rings", ""),
        ("bandnoise", "Band Noise", ""),
        ("ringnoise", "Ring Noise", ""),
    ]

    wood_noise_items = [
        ("sin", "Sin", ""),
        ("saw", "Saw", ""),
        ("tri", "Tri", ""),
    ]

    woodtype = EnumProperty(name="Type", description="Type of noise used", items=wood_type_items, default="bands")
    noisebasis = EnumProperty(name="Basis", description="Basis of noise used", items=NOISE_BASIS_ITEMS,
                                        default="blender_original")
    noisebasis2 = EnumProperty(name="Noise Basis 2", description="Second basis of noise used",
                                         items=wood_noise_items, default="sin")
    noisetype = EnumProperty(name="Noise Type", description="Soft or hard noise", items=NOISE_TYPE_ITEMS,
                                       default="soft_noise")

    def init(self, context):
        self.add_input("LuxCoreSocketFloatPositive", "Brightness", 1.0)
        self.add_input("LuxCoreSocketFloatPositive", "Contrast", 1.0)
        self.add_input("LuxCoreSocketFloatPositive", "Noisesize", 0.25)
        self.add_input("LuxCoreSocketFloatPositive", "Turbulence", 5.0)
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")

        self.outputs.new("LuxCoreSocketFloatPositive", "Float")

    def draw_buttons(self, context, layout):
        layout.prop(self, "noisebasis2", expand=True)
        layout.prop(self, "woodtype")
        if self.woodtype.endswith("noise"):
            layout.prop(self, "noisetype", expand=True)

    def export(self, props, luxcore_name=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(props)
       
        definitions = {
            "type": "blender_wood",
            "woodtype": self.woodtype,
            "noisebasis": self.noisebasis,
            "noisebasis2": self.noisebasis2,
            "noisetype": self.noisetype,
            "noisesize": self.inputs["Noisesize"].export(props),
            "turbulence": self.inputs["Turbulence"].export(props),
            "bright": self.inputs["Brightness"].export(props),
            "contrast": self.inputs["Contrast"].export(props),
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation),
        }
        
        return self.base_export(props, definitions, luxcore_name)
