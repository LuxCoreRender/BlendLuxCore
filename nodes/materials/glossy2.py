import bpy
from bpy.props import BoolProperty
from ..base import LuxCoreNodeMaterial, Roughness
from .glossytranslucent import IOR_DESCRIPTION, MULTIBOUNCE_DESCRIPTION
from ...utils import node as utils_node


class LuxCoreNodeMatGlossy2(LuxCoreNodeMaterial, bpy.types.Node):
    bl_label = "Glossy Material"
    bl_width_default = 160

    def update_use_ior(self, context):
        id = self.inputs.find("IOR")
        self.inputs[id].enabled = self.use_ior
        id = self.inputs.find("Specular Color")
        self.inputs[id].enabled = not self.use_ior
        utils_node.force_viewport_update(self, context)

    multibounce: BoolProperty(update=utils_node.force_viewport_update,
                              name="Multibounce",
                              default=False,
                              description=MULTIBOUNCE_DESCRIPTION)
    use_ior: BoolProperty(name="Use IOR",
                          default=False,
                          update=update_use_ior,
                          description=IOR_DESCRIPTION)
    use_anisotropy: BoolProperty(name=Roughness.aniso_name,
                                  default=False,
                                  description=Roughness.aniso_desc,
                                  update=Roughness.update_anisotropy)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Diffuse Color", [0.7] * 3)
        self.add_input("LuxCoreSocketColor", "Specular Color", [0.05] * 3)
        self.add_input("LuxCoreSocketIOR", "IOR", 1.5)
        self.inputs["IOR"].enabled = False
        self.add_input("LuxCoreSocketColor", "Absorption Color", [0] * 3)
        self.add_input("LuxCoreSocketFloatPositive", "Absorption Depth (nm)", 0)
        Roughness.init(self, 0.05)
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        layout.prop(self, "multibounce")
        layout.prop(self, "use_ior")
        Roughness.draw(self, context, layout)

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "glossy2",
            "kd": self.inputs["Diffuse Color"].export(exporter, depsgraph, props),
            "ka": self.inputs["Absorption Color"].export(exporter, depsgraph, props),
            "d": self.inputs["Absorption Depth (nm)"].export(exporter, depsgraph, props),
            "multibounce": self.multibounce,
        }

        if self.use_ior:
            definitions["index"] = self.inputs["IOR"].export(exporter, depsgraph, props)
            definitions["ks"] = [1, 1, 1]
        else:
            definitions["ks"] = self.inputs["Specular Color"].export(exporter, depsgraph, props)

        Roughness.export(self, exporter, depsgraph, props, definitions)
        self.export_common_inputs(exporter, depsgraph, props, definitions)
        return self.create_props(props, definitions, luxcore_name)
