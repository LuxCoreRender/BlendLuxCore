
from .. import LuxCoreNode


class luxcore_material_matte(LuxCoreNode):
    """Matte material node"""
    bl_idname = "luxcore_material_matte"
    bl_label = 'Matte Material'
    bl_icon = 'MATERIAL'
    bl_width_min = 160

    def init(self, context):
        pass
        # self.inputs.new('luxrender_TC_Kd_socket', 'Diffuse Color')
        # self.inputs.new('luxrender_TF_sigma_socket', 'Sigma')

    def export(self, properties):
        pass