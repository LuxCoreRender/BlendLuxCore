import bpy
from bpy.props import FloatProperty, BoolProperty
from .. import LuxCoreNodeMaterial, Roughness
from ..sockets import LuxCoreSocketFloat


class LuxCoreNodeMatGlass(LuxCoreNodeMaterial):
    """Glass material node"""
    bl_label = "Glass Material"
    bl_width_min = 160

    use_anisotropy = BoolProperty(name=Roughness.aniso_name,
                                  default=False,
                                  description=Roughness.aniso_desc,
                                  update=Roughness.update_anisotropy)
    rough = bpy.props.BoolProperty(name='Rough',
                                   description='Rough glass surface instead of a smooth one',
                                   default=False,
                                   update=Roughness.toggle_roughness)
    architectural = bpy.props.BoolProperty(name='Architectural',
                                           description='Skips refraction during transmission, propagates alpha and shadow rays',
                                           default=False)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Transmission Color", (1, 1, 1))
        self.add_input("LuxCoreSocketColor", "Reflection Color", (1, 1, 1))
        self.add_input("LuxCoreSocketIOR", "IOR", 1.5)

        Roughness.init(self, 0.1)

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        column = layout.row()
        column.enabled = not self.architectural
        column.prop(self, 'rough')

        if self.rough:
            column.prop(self, 'use_anisotropy')

        # Rough glass cannot be archglass
        row = layout.row()
        row.enabled = not self.rough
        row.prop(self, 'architectural')

    def export(self, props, luxcore_name=None):
        if self.rough:
            type = "roughglass"
        elif self.architectural:
            type = "archglass"
        else:
            type = "glass"

        definitions = {
            "type": type,
            "kt": self.inputs["Transmission Color"].export(props),
            "kr": self.inputs["Reflection Color"].export(props),
            "interiorior": self.inputs["IOR"].export(props),
        }
        if self.rough:
            Roughness.export(self, props, definitions)
        return self.base_export(props, definitions, luxcore_name)
