import bpy
from bpy.props import PointerProperty
from .. import LuxCoreNodeTexture
from ...export.image import ImageExporter


class LuxCoreNodeTexImagemap(LuxCoreNodeTexture):
    """Imagemap texture node"""
    bl_label = "Imagemap"
    bl_width_min = 160

    image = PointerProperty(name="Image", type=bpy.types.Image)

    def init(self, context):
        self.add_input("LuxCoreSocketFloatPositive", "Gamma", 2.2)
        self.add_input("LuxCoreSocketFloatPositive", "Gain", 1)

        self.outputs.new("LuxCoreSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "image")

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "imagemap",
            "file": ImageExporter.export(self.image),
            "gamma": self.inputs["Gamma"].export(props),
            "gain": self.inputs["Gain"].export(props),
        }
        return self.base_export(props, definitions, luxcore_name)
