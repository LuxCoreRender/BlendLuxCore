import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from .. import LuxCoreNodeMaterial, Roughness
from ..sockets import LuxCoreSocketColor, LuxCoreSocketFresnel
from .. import utils

class LuxCoreNodeMatMetal(LuxCoreNodeMaterial):
    """metal material node"""
    bl_label = "Metal Material"
    bl_width_min = 160

    def change_input_type(self, context):
        self.inputs['Fresnel'].enabled = self.input_type == 'fresnel'
        self.inputs['Color'].enabled = self.input_type == 'color'

    input_type_items = [
        ('color', 'Color', 'Use custom color as input'),
        ('fresnel', 'Fresnel Texture', 'Use a fresnel texture as input')
    ]
    input_type = EnumProperty(name='Type', description='Input Type', items=input_type_items, default='color',
                                        update=change_input_type)

    use_anisotropy = BoolProperty(name=Roughness.aniso_name,
                                  default=False,
                                  description=Roughness.aniso_desc,
                                  update=Roughness.update_anisotropy)

    def init(self, context):
        self.inputs.new('LuxCoreSocketColor', 'Color')
        self.inputs.new('LuxCoreSocketFresnel', 'Fresnel')
        self.inputs['Fresnel'].needs_link = True  # suppress inappropiate chooser
        self.inputs['Fresnel'].enabled = False        
        Roughness.init(self, 0.05)
        
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        column = layout.row()
        layout.prop(self, 'input_type', expand=True)
        Roughness.draw(self, context, layout)

    def export(self, props, luxcore_name=None):
        if self.input_type == 'fresnel':
            definitions = {
                "type": "metal2",
                "fresnel": self.inputs["Fresnel"].export(props),
            }

        else:            
            # Implicitly create a fresnelcolor texture
            node_tree = self.id_data
            name_parts = ["Fresnel", node_tree.name, "tex"]
            tex_name = utils.to_luxcore_name("_".join(name_parts))

            FCprefix = "scene.textures." + tex_name + "."

            fresnelcolor_defs = {
                "type": "fresnelcolor",
                "kr": self.inputs["Color"].export(props),
            }

            props.Set(utils.create_props(FCprefix, fresnelcolor_defs))

            definitions = {
                "type": "metal2",
                "fresnel": utils.to_luxcore_name("_".join(name_parts)),
            }
            
        Roughness.export(self, props, definitions)
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)
