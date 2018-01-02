import bpy
from bpy.props import FloatProperty, BoolProperty
from .. import LuxCoreNodeMaterial, Roughness
from ..output import get_active_output


class LuxCoreNodeMatGlass(LuxCoreNodeMaterial):
    bl_label = "Glass Material"
    bl_width_min = 160

    use_anisotropy = BoolProperty(name=Roughness.aniso_name,
                                  default=False,
                                  description=Roughness.aniso_desc,
                                  update=Roughness.update_anisotropy)
    rough = BoolProperty(name="Rough",
                         description="Rough glass surface instead of a smooth one",
                         default=False,
                         update=Roughness.toggle_roughness)
    architectural = BoolProperty(name="Architectural",
                                 description="Skips refraction during transmission, propagates alpha and shadow rays",
                                 default=False)
    ior = FloatProperty(name="IOR", default=1.5, min=1, soft_max=6, description="Index of refraction")
    dispersion = FloatProperty(name="Dispersion", default=0, min=0, soft_max=0.1, step=0.1, precision=3)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Transmission Color", (1, 1, 1))
        self.add_input("LuxCoreSocketColor", "Reflection Color", (1, 1, 1))
        # We use a property instead to disallow textured IOR for now
        # self.add_input("LuxCoreSocketIOR", "IOR", 1.5)

        Roughness.init(self, default=0.05, init_enabled=False)
        self.add_common_inputs()

        self.outputs.new("LuxCoreSocketMaterial", "Material")

    def draw_buttons(self, context, layout):
        column = layout.row()
        column.enabled = not self.architectural
        column.prop(self, "rough")

        if self.rough:
            Roughness.draw(self, context, layout)

        # Rough glass cannot be archglass
        row = layout.row()
        row.enabled = not self.rough
        row.prop(self, "architectural")

        if self._has_interior_volume():
            layout.label("Using IOR of interior volume", icon="INFO")
        else:
            col = layout.column(align=True)
            col.prop(self, "ior")
            col.prop(self, "dispersion")

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
            "dispersion": self.dispersion,
        }

        # Use IOR and dispersion only if there is no interior volume linked to the output
        if not self._has_interior_volume():
            if self.dispersion > 0:
                # Use an RGB IOR: three different refractive indices for red, green and blue
                # Prevent IOR below 1 (would lead to weird results)
                # TODO: maybe we should scale the spread with IOR? (higher IOR, higher spread - and at IOR 1 a spread of 0)
                red = max(self.ior - self.dispersion, 1.000001)
                green = self.ior
                blue = self.ior + self.dispersion
                definitions["interiorior"] = [red, green, blue]
                definitions["dispersion"] = True
            else:
                definitions["interiorior"] = self.ior
                definitions["dispersion"] = False

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
