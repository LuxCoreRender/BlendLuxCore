from bpy.props import EnumProperty, FloatProperty, IntProperty
from .. import LuxCoreNodeTexture
from .imagemap import NORMAL_SCALE_DESC


class LuxCoreNodeTexNormalmap(LuxCoreNodeTexture):
    bl_label = "Normalmap"

    scale = FloatProperty(name="Height", default=1, min=0, soft_max=5,
                          description=NORMAL_SCALE_DESC)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", [0.5, 0.5, 1])

        self.outputs.new("LuxCoreSocketBump", "Bump")

    def draw_buttons(self, context, layout):
        layout.prop(self, "scale")

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "normalmap",
            "texture": self.inputs["Color"].export(props),
            "scale": self.scale,
        }

        return self.base_export(props, definitions, luxcore_name)
