from bpy.props import EnumProperty, FloatProperty, IntProperty
from .. import LuxCoreNodeTexture
from ... import utils


class LuxCoreNodeTexBlenderNoise(LuxCoreNodeTexture):
    bl_label = "Blender Noise"
    bl_width_default = 200    

    noise_depth = IntProperty(name="Noise Depth", default=2, min=0)
    bright = FloatProperty(name="Brightness", default=1.0, min=0)
    contrast = FloatProperty(name="Contrast", default=1.0, min=0)

    def init(self, context):
        self.add_input("LuxCoreSocketMapping3D", "3D Mapping")
        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "noise_depth")
        layout.separator()
        column = layout.column(align=True)
        column.prop(self, "bright")
        column.prop(self, "contrast")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        mapping_type, transformation = self.inputs["3D Mapping"].export(exporter, props)
       
        definitions = {
            "type": "blender_noise",
            "noisedepth": self.noise_depth,
            "bright": self.bright,
            "contrast": self.contrast,
            # Mapping
            "mapping.type": mapping_type,
            "mapping.transformation": utils.matrix_to_list(transformation, exporter.scene, True),
        }
        
        return self.create_props(props, definitions, luxcore_name)
