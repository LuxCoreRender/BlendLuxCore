import bpy
from .. import LuxCoreNode


class luxcore_material_matte(LuxCoreNode):
    """(Rough) matte material node"""
    bl_label = "Matte Material"
    bl_width_min = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColorTex", "Diffuse Color", (0.7, 0.7, 0.7))
        self.add_input("LuxCoreSocketFloatTex", "Sigma", 0)

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def export(self, props):
        pass