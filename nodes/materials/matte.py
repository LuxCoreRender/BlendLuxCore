import bpy
from .. import LuxCoreNodeMaterial

class luxcore_material_matte(LuxCoreNodeMaterial):
    """(Rough) matte material node"""
    bl_label = "Matte Material"
    bl_width_min = 160

    def init(self, context):
        self.add_input("LuxCoreSocketColorTex", "Diffuse Color", (0.7, 0.7, 0.7))
        self.add_input("LuxCoreSocketFloatTex", "Sigma", 0)

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def export(self, props, luxcore_name=None):
        kd = self.inputs["Diffuse Color"].export(props)
        sigma = self.inputs["Sigma"].export(props)

        definitions = {
            "type": "roughmatte",
            "kd": kd,
            "sigma": sigma,
        }

        return self.base_export(props, definitions, luxcore_name)
