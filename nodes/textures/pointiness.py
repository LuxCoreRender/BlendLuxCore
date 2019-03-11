from bpy.props import FloatProperty, EnumProperty
from .. import LuxCoreNodeTexture
from ... import utils


class LuxCoreNodeTexPointiness(LuxCoreNodeTexture):
    bl_label = "Pointiness"
    bl_width_default = 180

    curvature_items = [
        ("concave", "Concave", "Only use dents"),
        ("convex", "Convex", "Only use hills"),
        ("both", "Both", "Use both hills and dents"),
    ]
    curvature_mode = EnumProperty(items=curvature_items, default="both")

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Multiplier", 10)
        
        self.outputs.new("LuxCoreSocketFloatUnbounded", "Value")

    def draw_buttons(self, context, layout):
        layout.prop(self, "curvature_mode", expand=True)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        # Pointiness is a hitpointalpha texture behind the scenes, just that it implicitly enables pointiness
        # calculation on the mesh (handled in luxcore object export) and has some nice wrapping to get only part of
        # the pointiness information (see code below)
        
        definitions = {
            "type": "hitpointalpha",
        }

        luxcore_name = self.create_props(props, definitions, luxcore_name)

        if self.curvature_mode == "both":
            # Pointiness values are in [-1..1] range originally
            name_abs = luxcore_name + "_abs"
            helper_prefix = "scene.textures." + name_abs + "."
            helper_defs = {
                "type": "abs",
                "texture": luxcore_name,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

            luxcore_name = name_abs

        elif self.curvature_mode == "concave":
            # Only use the positive values of the pointiness information
            name_clamp = luxcore_name + "_clamp"
            helper_prefix = "scene.textures." + name_clamp + "."
            helper_defs = {
                "type": "clamp",
                "texture": luxcore_name,
                "min": 0,
                "max": 1,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

            luxcore_name = name_clamp

        elif self.curvature_mode == "convex":
            # Only use the negative values of the pointiness information by first flipping the values
            name_flip = luxcore_name + "_flip"
            helper_prefix = "scene.textures." + name_flip + "."
            helper_defs = {
                "type": "scale",
                "texture1": luxcore_name,
                "texture2": -1,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

            name_clamp = luxcore_name + "_clamp"
            helper_prefix = "scene.textures." + name_clamp + "."
            helper_defs = {
                "type": "clamp",
                "texture": name_flip,
                "min": 0,
                "max": 1,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

            luxcore_name = name_clamp

        multiplier = self.inputs["Multiplier"].export(exporter, props)

        if multiplier != 1:
            multiplier_name = luxcore_name + "_multiplier"
            helper_prefix = "scene.textures." + multiplier_name + "."
            helper_defs = {
                "type": "scale",
                "texture1": luxcore_name,
                "texture2": multiplier,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

            luxcore_name = multiplier_name

        return luxcore_name
