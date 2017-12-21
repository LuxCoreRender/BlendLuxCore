import bpy
from bpy.props import FloatProperty, BoolProperty
from .. import LuxCoreNodeMaterial, Roughness
from ..output import get_active_output


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

        Roughness.init(self, default=0.1, init_enabled=False)
        self.add_common_inputs()

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

        if self._has_interior_volume():
            layout.label("Using IOR of interior volume", icon="INFO")

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
        }

        if not self._has_interior_volume():
            definitions["interiorior"] = self.inputs["IOR"].export(props)

        if self.rough:
            Roughness.export(self, props, definitions)
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)

    def _has_interior_volume(self):
        node_tree = self.id_data
        active_output = get_active_output(node_tree, "LuxCoreNodeMatOutput")
        if active_output:
            return active_output.interior_volume is not None
        return False
