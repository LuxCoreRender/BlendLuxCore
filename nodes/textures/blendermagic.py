from bpy.props import FloatProperty, IntProperty
from .. import LuxCoreNodeTexture

from ... import utils


class LuxCoreNodeTexBlenderMagic(LuxCoreNodeTexture):
    bl_label = "Blender Magic"
    bl_width_default = 200

    noise_depth = IntProperty(name="Noise Depth", default=2, min=0)
    turbulence = FloatProperty(name="Turbulence", default=5, min=0)
    bright = FloatProperty(name="Brightness", default=1.0, min=0)
    contrast = FloatProperty(name="Contrast", default=1.0, min=0)

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

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, props)
       
        definitions = {
            "type": "blender_magic",
            "noisedepth": self.noise_depth,
            "turbulence": self.turbulence,
            "bright": self.bright,
            "contrast": self.contrast,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }
        
        return self.create_props(props, definitions, luxcore_name)
