from bpy.props import FloatProperty, EnumProperty
from .. import LuxCoreNodeMaterial
from ..sockets import LuxCoreSocketFloat

REPEATU_DESCRIPTION = "Repetition count of pattern in U direction"
REPEATV_DESCRIPTION = "Repetition count of pattern in V direction"


class LuxCoreSocketRepeatU(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0, soft_max=10000, description=REPEATU_DESCRIPTION)
    slider = True


class LuxCoreSocketRepeatV(LuxCoreSocketFloat):
    default_value = FloatProperty(min=0, soft_max=10000, description=REPEATV_DESCRIPTION)
    slider = True


class LuxCoreNodeMatCloth(LuxCoreNodeMaterial):
    """Cloth material node"""
    bl_label = "Cloth Material"
    bl_width_min = 160

    preset_items = [
        ("denim", "Denim", "Denim", 0),
        ("silk_charmeuse", "Silk Charmeuse", "Silk charmeuse", 1),
        ("cotton_twill", "Cotton Twill", "Cotton twill", 2),
        ("wool_gabardine", "Wool Gabardine", "Wool Gabardine", 3),
        ("polyester_lining_cloth", "Polyester Lining Cloth", "Polyester lining cloth", 4),
        ("silk_shantung", "Silk Shantung", "Silk shantung", 5),
    ]

    preset = EnumProperty(name="Preset", description="Cloth presets", items=preset_items,
                          default="denim")
    
    def init(self, context):
        self.add_input("LuxCoreSocketRepeatU", "Repeat U", 100)
        self.add_input("LuxCoreSocketRepeatV", "Repeat V", 100)
        self.add_input("LuxCoreSocketColor", "Wrap Diffuse Color", (0.7, 0.05, 0.05))
        self.add_input("LuxCoreSocketColor", "Wrap Specular Color", (0.04, 0.04, 0.04))
        self.add_input("LuxCoreSocketColor", "Weft Diffuse Color", (0.64, 0.64, 0.64))
        self.add_input("LuxCoreSocketColor", "Weft Specular Color", (0.04, 0.04, 0.04))
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        layout.prop(self, "preset")

    def export(self, props, luxcore_name=None):
        definitions = {
            "type": "cloth",
            "preset": self.preset,
            "warp_kd": self.inputs["Wrap Diffuse Color"].export(props),
            "warp_ks": self.inputs["Wrap Specular Color"].export(props),
            "weft_kd": self.inputs["Weft Diffuse Color"].export(props),
            "weft_ks": self.inputs["Weft Specular Color"].export(props),
            "repeat_u": self.inputs["Repeat U"].export(props),
            "repeat_v": self.inputs["Repeat V"].export(props)
        }
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
