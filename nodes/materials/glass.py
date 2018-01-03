import bpy
from bpy.props import FloatProperty, BoolProperty
from .. import LuxCoreNodeMaterial, Roughness
from ..output import get_active_output
from .. import utils
from ...utils import node as utils_node


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
    dispersion = FloatProperty(name="Dispersion", default=0, min=0, soft_max=0.1, step=0.1, precision=3)

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Transmission Color", (1, 1, 1))
        self.add_input("LuxCoreSocketColor", "Reflection Color", (1, 1, 1))
        self.add_input("LuxCoreSocketIOR", "IOR", 1.5)

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

        layout.prop(self, "dispersion")

        if self.get_interior_volume():
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
            "dispersion": self.dispersion > 0,
        }

        # If we have an interior volume, we use its IOR instead of the glass IOR
        interior_vol = self.get_interior_volume()

        if interior_vol:
            out = get_active_output(interior_vol, "LuxCoreNodeVolOutput")
            vol_node = utils_node.get_linked_node(out.inputs["Volume"])
            if vol_node:
                ior = vol_node.inputs["IOR"].export(props)
                is_textured_ior = vol_node.inputs["IOR"].is_linked
            else:
                raise Exception("ERROR in glass node export: can't find interior volume IOR")
        else:
            ior = self.inputs["IOR"].export(props)
            is_textured_ior = self.inputs["IOR"].is_linked

        if self.dispersion > 0:
            # TODO: maybe we should scale the spread with IOR? (higher IOR, higher spread - and at IOR 1 a spread of 0)
            if is_textured_ior:
                # Create helper texture with unique name
                node_tree = self.id_data
                name_parts = ["dispersion", node_tree.name, self.name]
                helper_name = utils.to_luxcore_name("_".join(name_parts))

                helper_prefix = "scene.textures." + helper_name + "."
                helper_defs = {
                    "type": "add",
                    "texture1": ior,
                    "texture2": [-self.dispersion, 0, self.dispersion]
                }
                props.Set(utils.create_props(helper_prefix, helper_defs))

                definitions["interiorior"] = helper_name
            else:
                # IOR is not textured, just a simple value
                # Prevent IOR below 1 (would lead to weird results)
                red = max(ior - self.dispersion, 1.000001)
                green = ior
                blue = ior + self.dispersion
                definitions["interiorior"] = [red, green, blue]
        else:
            definitions["interiorior"] = ior

        if self.rough:
            Roughness.export(self, props, definitions)
        self.export_common_inputs(props, definitions)
        return self.base_export(props, definitions, luxcore_name)

    def get_interior_volume(self):
        node_tree = self.id_data
        active_output = get_active_output(node_tree, "LuxCoreNodeMatOutput")
        if active_output:
            return active_output.interior_volume
        return False
