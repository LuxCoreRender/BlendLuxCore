from bpy.props import EnumProperty, FloatProperty, IntProperty
from .. import LuxCoreNodeTexture

from .. import NOISE_BASIS_ITEMS
from .. import NOISE_TYPE_ITEMS

from ... import utils


class LuxCoreNodeTexBlenderStucci(LuxCoreNodeTexture):
    bl_label = "Blender Stucci"
    bl_width_default = 200    

    stucci_type_items = [
        ("plastic", "Plastic", ""),
        ("wall_in", "Wall In", ""),
        ("wall_out", "Wall Out", ""),
    ]

    stucci_type = EnumProperty(name="Type", description="Type of noise used", items=stucci_type_items, default="plastic")
    noise_basis = EnumProperty(name="Basis", description="Basis of noise used", items=NOISE_BASIS_ITEMS,
                                        default="blender_original")
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
        layout.prop(self, "stucci_type", expand=True)
        layout.prop(self, "noise_basis")
        layout.prop(self, "noise_type", expand=True)

        col = layout.column(align=True)
        col.prop(self, "noise_size")
        col.prop(self, "turbulence")

        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, props)
       
        definitions = {
            "type": "blender_stucci",
            "stuccitype": self.stucci_type,
            "noisebasis": self.noise_basis,
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
