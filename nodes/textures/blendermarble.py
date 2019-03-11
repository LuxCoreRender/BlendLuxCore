from bpy.props import EnumProperty, IntProperty, FloatProperty
from .. import LuxCoreNodeTexture

from .. import NOISE_BASIS_ITEMS
from .. import NOISE_TYPE_ITEMS

from ... import utils


class LuxCoreNodeTexBlenderMarble(LuxCoreNodeTexture):
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

    marble_type = EnumProperty(name="Type", description="Type of noise used", items=marble_type_items, default="soft")
    noise_basis = EnumProperty(name="Noise Basis", description="Basis of noise used", items=NOISE_BASIS_ITEMS,
                                        default="blender_original")
    noise_basis2 = EnumProperty(name="Noise Basis 2", description="Second basis of noise used",
                                         items=marble_noise_items, default="sin")
    noise_type = EnumProperty(name="Noise Type", description="Soft or hard noise", items=NOISE_TYPE_ITEMS,
                                       default="soft_noise")
    noise_size = FloatProperty(name="Noise Size", default=0.25, min=0)
    noise_depth = IntProperty(name="Noise Depth", default=2, min=0)
    turbulence = FloatProperty(name="Turbulence", default=5.0, min=0)
    bright = FloatProperty(name="Brightness", default=1.0, min=0)
    contrast = FloatProperty(name="Contrast", default=1.0, min=0)

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

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, props)
       
        definitions = {
            "type": "blender_marble",
            "noisebasis": self.noise_basis,
            "noisebasis2": self.noise_basis2,
            "noisetype": self.noise_type,
            "noisesize": self.noise_size,
            "turbulence": self.turbulence,
            "bright": self.bright,
            "contrast": self.contrast,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }
        
        return self.create_props(props, definitions, luxcore_name)
