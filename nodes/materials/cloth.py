import bpy
from bpy.props import FloatProperty, EnumProperty
from ..base import LuxCoreNodeMaterial
from ..sockets import LuxCoreSocketFloat
from ...utils import node as utils_node

REPEATU_DESCRIPTION = "Repetition count of pattern in U direction"
REPEATV_DESCRIPTION = "Repetition count of pattern in V direction"


# Note: we need to keep this class around for backwards compatibility reasons,
# even if it is not used (we need it so we can port old cloth nodes to new ones)
class LuxCoreSocketRepeatU(bpy.types.NodeSocket, LuxCoreSocketFloat):
    default_value: FloatProperty(min=0, soft_max=10000, description=REPEATU_DESCRIPTION)
    slider = True


# Note: we need to keep this class around for backwards compatibility reasons,
# even if it is not used (we need it so we can port old cloth nodes to new ones)
class LuxCoreSocketRepeatV(bpy.types.NodeSocket, LuxCoreSocketFloat):
    default_value: FloatProperty(min=0, soft_max=10000, description=REPEATV_DESCRIPTION)
    slider = True


class LuxCoreNodeMatCloth(LuxCoreNodeMaterial, bpy.types.Node):
    """Cloth material node"""
    bl_label = "Cloth Material"
    bl_width_default = 160

    preset_items = [
        ("denim", "Denim", "", 0),
        ("silk_charmeuse", "Silk Charmeuse", "", 1),
        ("cotton_twill", "Cotton Twill", "", 2),
        ("wool_gabardine", "Wool Gabardine", "", 3),
        ("polyester_lining_cloth", "Polyester Lining Cloth", "", 4),
        ("silk_shantung", "Silk Shantung", "", 5),
    ]

    preset: EnumProperty(update=utils_node.force_viewport_update, name="Preset", description="Cloth presets", items=preset_items,
                          default="denim")

    repeat_u: FloatProperty(update=utils_node.force_viewport_update, name="Repeat U", default=100, min=0, soft_max=10000,
                             description=REPEATU_DESCRIPTION)
    repeat_v: FloatProperty(update=utils_node.force_viewport_update, name="Repeat V", default=100, min=0, soft_max=10000,
                             description=REPEATV_DESCRIPTION)
    
    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Wrap Diffuse Color", (0.7, 0.05, 0.05))
        self.add_input("LuxCoreSocketColor", "Wrap Specular Color", (0.04, 0.04, 0.04))
        self.add_input("LuxCoreSocketColor", "Weft Diffuse Color", (0.64, 0.64, 0.64))
        self.add_input("LuxCoreSocketColor", "Weft Specular Color", (0.04, 0.04, 0.04))
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        # Info about UV mapping (only show if default is used,
        utils_node.draw_uv_info(context, layout)

        col = layout.column(align=True)
        col.prop(self, "repeat_u", slider=True)
        col.prop(self, "repeat_v", slider=True)

        layout.prop(self, "preset")

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "cloth",
            "preset": self.preset,
            "warp_kd": self.inputs["Wrap Diffuse Color"].export(exporter, depsgraph, props),
            "warp_ks": self.inputs["Wrap Specular Color"].export(exporter, depsgraph, props),
            "weft_kd": self.inputs["Weft Diffuse Color"].export(exporter, depsgraph, props),
            "weft_ks": self.inputs["Weft Specular Color"].export(exporter, depsgraph, props),
            "repeat_u": self.repeat_u,
            "repeat_v": self.repeat_v,
        }
        self.export_common_inputs(exporter, depsgraph, props, definitions)
        return self.create_props(props, definitions, luxcore_name)
