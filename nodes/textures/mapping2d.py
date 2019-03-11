import math
from bpy.props import FloatProperty, BoolProperty
from .. import LuxCoreNodeTexture
from ...utils import node as utils_node


class LuxCoreNodeTexMapping2D(LuxCoreNodeTexture):
    bl_label = "2D Mapping"
    bl_width_default = 160

    def update_uniform_scale(self, context):
        self["uscale"] = self.uniform_scale
        self["vscale"] = self.uniform_scale

    # TODO descriptions
    use_uniform_scale = BoolProperty(name="Uniform Scale", default=True)
    uniform_scale = FloatProperty(name="UV Scale", default=1, update=update_uniform_scale)
    uscale = FloatProperty(name="U", default=1)
    vscale = FloatProperty(name="V", default=1)
    rotation = FloatProperty(name="Rotation", default=0, min=(-math.pi * 2),
                             max=(math.pi * 2), subtype="ANGLE", unit="ROTATION")
    udelta = FloatProperty(name="U", default=0)
    vdelta = FloatProperty(name="V", default=0)
    center_map = BoolProperty(name="Center Map", default=False)

    def init(self, context):
        # Instead of creating a new mapping, the user can also
        # manipulate an existing mapping
        self.add_input("LuxCoreSocketMapping2D", "2D Mapping (optional)")

        self.outputs.new("LuxCoreSocketMapping2D", "2D Mapping")

    def draw_buttons(self, context, layout):
        # Info about UV mapping so the user can react if no UV map etc.
        utils_node.draw_uv_info(context, layout)

        layout.prop(self, "center_map")
        layout.prop(self, "use_uniform_scale")

        if self.use_uniform_scale:
            layout.prop(self, "uniform_scale")
        else:
            row = layout.row(align=True)
            row.prop(self, "uscale")
            row.prop(self, "vscale")

        layout.prop(self, "rotation")

        layout.label("Offset:")
        row = layout.row(align=True)
        row.prop(self, "udelta")
        row.prop(self, "vdelta")

    def export(self, exporter, props, luxcore_name=None, output_socket=None):
        input_uvscale, input_rotation, input_uvdelta = self.inputs["2D Mapping (optional)"].export(exporter, props)

        # Scale
        if self.use_uniform_scale:
            uvscale = [self.uniform_scale, self.uniform_scale]
        else:
            uvscale = [self.uscale, self.vscale]
        output_uvscale = [a * b for a, b in zip(input_uvscale, uvscale)]

        # Rotation
        rotation = math.degrees(self.rotation)
        output_rotation = input_rotation + rotation

        # Translation
        if self.center_map:
            uvdelta = [self.udelta + 0.5 * (1 - uvscale[0]),
                       self.vdelta * -1 + 1 - (0.5 * (1 - uvscale[1]))]
        else:
            uvdelta = [self.udelta,
                       self.vdelta + 1]

        output_uvdelta = [a + b for a, b in zip(input_uvdelta, uvdelta)]

        return output_uvscale, output_rotation, output_uvdelta
