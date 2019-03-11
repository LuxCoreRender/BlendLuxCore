import bpy
from bpy.props import FloatProperty
from .. import LuxCoreNodeTexture
from ..sockets import LuxCoreSocketFloat
from ... import utils


class LuxCoreSocketBumpHeight(LuxCoreSocketFloat):
    # Allow negative values for inverting the bump. These values are in meters.
    default_value = FloatProperty(default=0.001, soft_min=-0.01, soft_max=0.01,
                                  precision=3, step=0.001,
                                  subtype="DISTANCE", description="Bump height")


class LuxCoreNodeTexBump(LuxCoreNodeTexture):
    """ A scale texture which applies worldscale """
    bl_label = "Bump"
    bl_width_default = 180

    def init(self, context):
        self.add_input("LuxCoreSocketFloatUnbounded", "Value", 0.0)
        self.add_input("LuxCoreSocketBumpHeight", "Bump Height", 0.001)

        self.outputs.new("LuxCoreSocketBump", "Bump")

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        definitions = {
            "type": "scale",
            "texture1": self.inputs["Value"].export(exporter, props),
        }

        bump_height = self.inputs["Bump Height"].export(exporter, props)
        worldscale = utils.get_worldscale(exporter.scene, as_scalematrix=False)

        if self.inputs["Bump Height"].is_linked:
            # Bump height is textured, we need a scale texture to apply worldscale
            tex_name = self.make_name() + "bump_helper"
            helper_prefix = "scene.textures." + tex_name + "."
            helper_defs = {
                "type": "scale",
                "texture1": bump_height,
                "texture2": worldscale,
            }
            props.Set(utils.create_props(helper_prefix, helper_defs))

            definitions["texture2"] = tex_name
        else:
            # Bump height is just a value, we can apply worldscale directly
            definitions["texture2"] = bump_height * worldscale

        return self.create_props(props, definitions, luxcore_name)
